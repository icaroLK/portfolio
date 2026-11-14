from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("portfolio:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "portfolio/home.html")

    def test_home_page_loads_css_and_fonts(self):
        response = self.client.get("/")
        self.assertContains(response, "css/site.css")
        self.assertContains(response, "family=Inter:")


class AdminPathTests(TestCase):
    def test_default_admin_path_is_hidden(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    def test_private_admin_path_works(self):
        response = self.client.get(f"/{settings.ADMIN_PATH}/")
        # Not logged in, so Django redirects to the admin login page.
        self.assertEqual(response.status_code, 302)
