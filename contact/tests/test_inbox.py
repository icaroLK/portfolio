from datetime import timedelta

from django.conf import settings
from django.test import TestCase

from contact.models import ContactMessage
from portfolio.tests.helpers import AdminLoginMixin

INBOX = f"/{settings.ADMIN_PATH}/contact/contactmessage/"


class ContactMessageModelTests(TestCase):
    def test_newest_first(self):
        old = ContactMessage.objects.create(name="Old", email="a@x.com", message="hello there")
        new = ContactMessage.objects.create(name="New", email="b@x.com", message="hello again")
        # Both rows can get the same timestamp on a fast machine, so push "old" back a day.
        ContactMessage.objects.filter(pk=old.pk).update(created_at=old.created_at - timedelta(days=1))
        self.assertEqual(list(ContactMessage.objects.all()), [new, old])

    def test_str_shows_name_and_topic(self):
        message = ContactMessage(name="Ana", email="a@x.com", topic="job", message="hi")
        self.assertEqual(str(message), "Ana (Job opportunity)")


class InboxAdminTests(AdminLoginMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.first = ContactMessage.objects.create(name="A", email="a@x.com", message="hello there")
        self.second = ContactMessage.objects.create(name="B", email="b@x.com", message="hello again")

    def test_title_shows_unread_count(self):
        self.assertContains(self.client.get(INBOX), "Inbox (2 unread)")

    def test_no_add_button(self):
        self.assertNotContains(self.client.get(INBOX), f"{INBOX}add/")
        self.assertEqual(self.client.get(f"{INBOX}add/").status_code, 403)

    def test_messages_are_read_only(self):
        url = f"{INBOX}{self.first.pk}/change/"
        self.assertNotContains(self.client.get(url), 'name="_save"')
        self.client.post(url, {"name": "Changed", "email": "a@x.com", "message": "changed text"})
        self.first.refresh_from_db()
        self.assertEqual(self.first.name, "A")

    def test_bulk_actions(self):
        self.client.post(INBOX, {"action": "mark_as_read", "_selected_action": [self.first.pk]})
        self.client.post(INBOX, {"action": "mark_as_spam", "_selected_action": [self.second.pk]})
        self.first.refresh_from_db()
        self.second.refresh_from_db()
        self.assertTrue(self.first.is_read)
        self.assertTrue(self.second.is_spam)
        self.assertContains(self.client.get(INBOX), "Inbox (0 unread)")
