"""Behavior that only matters on the live server, behind Cloudflare."""

import importlib

from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from config.client_ip import client_ip
from portfolio.models import SiteSettings


class ClientIpTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_uses_remote_addr_by_default(self):
        request = self.factory.get("/", REMOTE_ADDR="1.2.3.4", HTTP_CF_CONNECTING_IP="6.6.6.6")
        self.assertEqual(client_ip(request), "1.2.3.4")

    @override_settings(CLIENT_IP_HEADER="HTTP_CF_CONNECTING_IP")
    def test_reads_cloudflare_header_when_set(self):
        request = self.factory.get("/", REMOTE_ADDR="127.0.0.1", HTTP_CF_CONNECTING_IP="2001:db8::1")
        self.assertEqual(client_ip(request), "2001:db8::1")

    @override_settings(CLIENT_IP_HEADER="HTTP_CF_CONNECTING_IP")
    def test_falls_back_when_header_missing(self):
        request = self.factory.get("/", REMOTE_ADDR="127.0.0.1")
        self.assertEqual(client_ip(request), "127.0.0.1")


@override_settings(
    CANONICAL_HOST="icarokucha.com",
    ALLOWED_HOSTS=["icarokucha.com", "www.icarokucha.com"],
)
class CanonicalHostTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteSettings.objects.create(site_name="Test Name", headline="H")

    def test_www_redirects_to_apex_keeping_the_path(self):
        response = self.client.get("/about/?sent=1", HTTP_HOST="www.icarokucha.com")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "https://icarokucha.com/about/?sent=1")

    def test_apex_is_served_normally(self):
        response = self.client.get("/healthz/", HTTP_HOST="icarokucha.com")
        self.assertEqual(response.status_code, 200)


class ProductionSettingsTests(SimpleTestCase):
    """Reads prod.py as a plain module (it does not switch the running settings)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prod = importlib.import_module("config.settings.prod")

    def test_debug_is_off(self):
        self.assertFalse(self.prod.DEBUG)

    def test_trusts_cloudflare_for_https_and_visitor_ip(self):
        self.assertEqual(self.prod.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))
        self.assertTrue(self.prod.SECURE_SSL_REDIRECT)
        self.assertEqual(self.prod.CLIENT_IP_HEADER, "HTTP_CF_CONNECTING_IP")

    def test_cookies_are_secure(self):
        self.assertTrue(self.prod.SESSION_COOKIE_SECURE)
        self.assertTrue(self.prod.CSRF_COOKIE_SECURE)

    def test_errors_are_logged_to_a_file(self):
        self.assertIn("file", self.prod.LOGGING["handlers"])
