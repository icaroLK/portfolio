"""The production email path: contact notifications through Resend's HTTP API.

The network call is faked, so these tests never send a real email.
"""

import json
from unittest import mock

import requests
from django.test import TestCase, override_settings
from django.urls import reverse

from contact.models import ContactMessage
from portfolio.models import SiteSettings

RESEND = {
    "EMAIL_BACKEND": "anymail.backends.resend.EmailBackend",
    "ANYMAIL": {"RESEND_API_KEY": "re_test_key"},
    "DEFAULT_FROM_EMAIL": "Site <site@icarokucha.com>",
}

VALID = {
    "name": "Ana",
    "email": "ana@example.com",
    "topic": "job",
    "message": "We have a Django role for you.",
    "website": "",
}


def fake_response(status, body):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode()
    response.headers["Content-Type"] = "application/json"
    return response


@override_settings(**RESEND)
class ResendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteSettings.objects.create(site_name="Test Name", headline="H", notification_email="me@example.com")

    def submit(self, response):
        with mock.patch.object(requests.Session, "request", return_value=response) as call:
            self.client.post(reverse("contact:submit"), VALID, REMOTE_ADDR="1.2.3.4")
        return call

    def test_sends_to_resend_api(self):
        call = self.submit(fake_response(200, {"id": "email-123"}))
        args, kwargs = call.call_args
        method, url = args[:2] if args else (kwargs["method"], kwargs["url"])
        payload = json.loads(kwargs["data"])
        self.assertEqual((method.upper(), url), ("POST", "https://api.resend.com/emails"))
        self.assertEqual(payload["to"], ["me@example.com"])
        self.assertEqual(payload["from"], "Site <site@icarokucha.com>")
        self.assertEqual(payload["reply_to"], ["ana@example.com"])
        self.assertIn("We have a Django role for you.", payload["text"])
        self.assertTrue(ContactMessage.objects.get().email_sent)

    def test_provider_error_still_saves_the_message(self):
        with self.assertLogs("contact.notifications", level="ERROR"):
            self.submit(fake_response(500, {"message": "down"}))
        message = ContactMessage.objects.get()
        self.assertFalse(message.email_sent)
