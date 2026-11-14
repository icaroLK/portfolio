from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from contact.models import ContactMessage
from portfolio.models import SiteSettings

SUBMIT = reverse("contact:submit")
SENT_URL = reverse("portfolio:about") + "?sent=1#contact"

VALID = {
    "name": "Ana",
    "email": "ana@example.com",
    "topic": "business",
    "message": "I need a booking system for my shop.",
    "website": "",
}


class ContactFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteSettings.objects.create(
            site_name="Test Name", headline="H", notification_email="me@example.com"
        )

    def post(self, data=None, ip="1.2.3.4", **extra):
        return self.client.post(SUBMIT, data or VALID, REMOTE_ADDR=ip, **extra)


class ValidSubmissionTests(ContactFormTestCase):
    def test_saves_message_and_redirects(self):
        response = self.post(HTTP_USER_AGENT="TestBrowser/1.0")
        self.assertRedirects(response, SENT_URL)
        message = ContactMessage.objects.get()
        self.assertEqual(message.name, "Ana")
        self.assertEqual(message.topic, "business")
        self.assertEqual(message.ip_address, "1.2.3.4")
        self.assertEqual(message.user_agent, "TestBrowser/1.0")
        self.assertFalse(message.is_read)

    def test_sends_notification_email(self):
        self.post()
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["me@example.com"])
        self.assertEqual(email.reply_to, ["ana@example.com"])
        self.assertIn("Ana", email.subject)
        self.assertIn("booking system", email.body)
        self.assertTrue(ContactMessage.objects.get().email_sent)

    def test_success_page_shows_message(self):
        response = self.post()
        self.assertContains(self.client.get(response.url), "your message was sent")

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(SUBMIT).status_code, 405)


class EmailFailureTests(ContactFormTestCase):
    def test_provider_down_still_saves_and_logs(self):
        with mock.patch("contact.notifications.EmailMessage.send", side_effect=OSError("down")):
            with self.assertLogs("contact.notifications", level="ERROR"):
                response = self.post()
        self.assertRedirects(response, SENT_URL)
        self.assertFalse(ContactMessage.objects.get().email_sent)

    def test_no_notification_address_still_saves(self):
        SiteSettings.objects.filter(pk=1).update(notification_email="")
        with self.assertLogs("contact.notifications", level="WARNING"):
            self.post()
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(ContactMessage.objects.get().email_sent)


class InvalidSubmissionTests(ContactFormTestCase):
    def test_empty_form_shows_errors(self):
        response = self.post({"name": "", "email": "", "message": "", "topic": "job"})
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, "portfolio/about.html")
        for field in ["name", "email", "message"]:
            self.assertContains(response, f'id="id_{field}_error"', status_code=400)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_errors_keep_input(self):
        data = {**VALID, "email": "not-an-email", "message": "short"}
        response = self.post(data)
        self.assertContains(response, 'value="Ana"', status_code=400)
        self.assertContains(response, 'value="not-an-email"', status_code=400)
        self.assertContains(response, "short</textarea>", status_code=400)
        self.assertContains(response, "Enter a valid email address.", status_code=400)
        self.assertContains(response, "at least 10 characters", status_code=400)

    def test_invalid_field_is_marked_for_screen_readers(self):
        response = self.post({**VALID, "email": "nope"})
        self.assertContains(response, 'aria-invalid="true"', status_code=400)
        self.assertContains(response, 'aria-describedby="id_email_error"', status_code=400)

    def test_message_too_long(self):
        response = self.post({**VALID, "message": "x" * 5001})
        self.assertContains(response, "at most 5000 characters", status_code=400)

    def test_unknown_topic_rejected(self):
        response = self.post({**VALID, "topic": "hack"})
        self.assertEqual(response.status_code, 400)


class HoneypotTests(ContactFormTestCase):
    def test_filled_honeypot_is_silently_dropped(self):
        response = self.post({**VALID, "website": "http://spam.example"})
        self.assertRedirects(response, SENT_URL)  # looks like success to the bot
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_honeypot_is_hidden_from_people(self):
        response = self.client.get(reverse("portfolio:about"))
        self.assertContains(response, 'name="website"')
        self.assertContains(response, 'tabindex="-1"')
        self.assertContains(response, 'aria-hidden="true"')


class RateLimitTests(ContactFormTestCase):
    def test_fourth_message_in_an_hour_is_blocked(self):
        for _ in range(3):
            self.assertRedirects(self.post(), SENT_URL)
        response = self.post()
        self.assertContains(response, "Please try again later", status_code=400)
        self.assertContains(response, 'value="Ana"', status_code=400)  # input kept
        self.assertEqual(ContactMessage.objects.count(), 3)

    def test_other_visitors_are_not_blocked(self):
        for _ in range(3):
            self.post(ip="1.2.3.4")
        self.assertRedirects(self.post(ip="5.6.7.8"), SENT_URL)

    def test_limit_resets_after_an_hour(self):
        for _ in range(3):
            self.post()
        ContactMessage.objects.update(created_at=ContactMessage.objects.first().created_at - timedelta(hours=2))
        self.assertRedirects(self.post(), SENT_URL)

    def test_forwarded_header_ignored_by_default(self):
        # Without a trusted proxy, a fake X-Forwarded-For must not dodge the limit.
        for i in range(3):
            self.post(HTTP_X_FORWARDED_FOR=f"9.9.9.{i}")
        self.assertEqual(self.post(HTTP_X_FORWARDED_FOR="9.9.9.99").status_code, 400)

    @override_settings(TRUST_X_FORWARDED_FOR=True)
    def test_behind_proxy_uses_last_forwarded_address(self):
        self.post(ip="10.0.0.1", HTTP_X_FORWARDED_FOR="6.6.6.6, 203.0.113.7")
        self.assertEqual(ContactMessage.objects.get().ip_address, "203.0.113.7")


class FormToggleTests(ContactFormTestCase):
    def test_turned_off_form_rejects_posts(self):
        SiteSettings.objects.filter(pk=1).update(show_contact_form=False)
        response = self.post()
        self.assertRedirects(response, reverse("portfolio:about") + "#contact")
        self.assertEqual(ContactMessage.objects.count(), 0)


class RefreshTests(ContactFormTestCase):
    def test_success_page_is_a_plain_get(self):
        # POST/redirect/GET: the page a refresh reloads is a GET, so nothing is resent.
        response = self.post(follow=True)
        self.assertEqual(response.request["REQUEST_METHOD"], "GET")
        self.client.get(SENT_URL)
        self.assertEqual(ContactMessage.objects.count(), 1)
