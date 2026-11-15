"""Admin login lockout (django-axes): 5 wrong passwords lock that IP for an hour."""

from axes.models import AccessAttempt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from portfolio.models import SiteSettings

LOGIN = reverse("admin:login")


class AdminLockoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteSettings.objects.create(site_name="Test Name", headline="H")
        get_user_model().objects.create_superuser("icaro", "i@example.com", "right-pass-123")

    def login(self, password, **extra):
        return self.client.post(
            LOGIN, {"username": "icaro", "password": password}, REMOTE_ADDR="1.2.3.4", **extra
        )

    def test_a_few_wrong_passwords_only_show_the_form_again(self):
        for _ in range(4):
            self.assertEqual(self.login("wrong").status_code, 200)

    def test_five_wrong_passwords_lock_the_login(self):
        for _ in range(5):
            self.login("wrong")
        response = self.login("right-pass-123")  # even the right password is refused now
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Try again in an hour", status_code=429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_lockout_lasts_one_hour(self):
        for _ in range(5):
            self.login("wrong")
        attempt = AccessAttempt.objects.get()
        self.assertEqual(attempt.ip_address, "1.2.3.4")
        self.assertEqual(settings.AXES_COOLOFF_TIME.total_seconds(), 3600)

    def test_right_password_resets_the_count(self):
        for _ in range(4):
            self.login("wrong")
        self.assertEqual(self.login("right-pass-123").status_code, 302)
        self.assertFalse(AccessAttempt.objects.exists())

    @override_settings(CLIENT_IP_HEADER="HTTP_CF_CONNECTING_IP")
    def test_behind_cloudflare_lock_is_per_visitor(self):
        for _ in range(5):
            self.login("wrong", HTTP_CF_CONNECTING_IP="203.0.113.7")
        self.assertEqual(self.login("wrong", HTTP_CF_CONNECTING_IP="203.0.113.7").status_code, 429)
        # Someone else (you, from home) can still log in.
        response = self.login("right-pass-123", HTTP_CF_CONNECTING_IP="198.51.100.2")
        self.assertEqual(response.status_code, 302)
