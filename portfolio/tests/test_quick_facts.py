"""About page quick facts: location, local time, links with icons and languages."""

import io
from datetime import datetime, timezone as dt_timezone
from unittest import mock

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from portfolio.models import Language, Service, SiteSettings

from .helpers import AdminLoginMixin, TempMediaMixin

ABOUT = reverse("portfolio:about")
ADMIN = f"/{settings.ADMIN_PATH}/"
# 21:15 UTC is 18:15 in São Paulo (UTC-3, no daylight saving time).
FIXED_NOW = datetime(2026, 11, 15, 21, 15, tzinfo=dt_timezone.utc)


def make_site(**extra):
    fields = {
        "site_name": "Test Name",
        "headline": "H",
        "about_location": "Curitiba, Brazil",
        "time_zone": "America/Sao_Paulo",
        "email": "hi@example.com",
        "github_url": "https://github.com/icaroLK",
        "linkedin_url": "https://www.linkedin.com/in/icaro-test/",
        "about_bio": "I'm an **AI engineer**.\nWhat I do:\n   · Pipelines\n   · Agents",
        **extra,
    }
    site = SiteSettings(**fields)
    site.save()
    return site


class SiteSettingsFactTests(TestCase):
    def test_profile_handles_come_from_the_links(self):
        site = make_site()
        self.assertEqual(site.github_handle, "icaroLK")
        self.assertEqual(site.linkedin_handle, "in/icaro-test")

    def test_handles_are_empty_without_links(self):
        site = make_site(github_url="", linkedin_url="")
        self.assertEqual(site.github_handle, "")
        self.assertEqual(site.linkedin_handle, "")

    def test_utc_offset_label(self):
        with mock.patch("django.utils.timezone.now", return_value=FIXED_NOW):
            self.assertEqual(make_site().utc_offset_label, "UTC-03:00")
            self.assertEqual(make_site(time_zone="Asia/Kolkata").utc_offset_label, "UTC+05:30")
            self.assertEqual(make_site(time_zone="").utc_offset_label, "")

    def test_unknown_time_zone_is_rejected(self):
        site = make_site()
        site.time_zone = "Mars/Olympus"
        with self.assertRaises(ValidationError):
            site.full_clean()

    def test_languages_follow_admin_order(self):
        site = make_site()
        Language.objects.create(site=site, name="English", level="C1", order=1)
        Language.objects.create(site=site, name="Portuguese", level="Native", order=0)
        self.assertEqual([str(lang) for lang in site.languages.all()],
                         ["Portuguese (Native)", "English (C1)"])


class AboutQuickFactsPageTests(TestCase):
    def setUp(self):
        self.site = make_site()
        Language.objects.create(site=self.site, name="English", level="C1", order=1)
        Language.objects.create(site=self.site, name="Portuguese", level="Native", order=0)

    def test_facts_show_with_their_values(self):
        with mock.patch("django.utils.timezone.now", return_value=FIXED_NOW):
            response = self.client.get(ABOUT)
        self.assertContains(response, 'aria-label="Quick facts"')
        self.assertContains(response, "Curitiba, Brazil")
        self.assertContains(response, ">18:15<")
        self.assertContains(response, "(UTC-03:00)")
        self.assertContains(response, 'data-tz="America/Sao_Paulo"')
        self.assertContains(response, 'href="mailto:hi@example.com"')
        self.assertContains(response, ">icaroLK<")
        self.assertContains(response, "in/icaro-test<")
        self.assertContains(response, "js/clock.js")

    def test_languages_in_order_with_levels(self):
        html = self.client.get(ABOUT).content.decode()
        self.assertIn("languages-heading", html)
        self.assertLess(html.index("Portuguese"), html.index("English"))
        self.assertIn(">Native<", html)
        self.assertIn(">C1<", html)

    def test_bio_renders_formatting_and_dot_list(self):
        response = self.client.get(ABOUT)
        self.assertContains(response, "<strong>AI engineer</strong>")
        self.assertContains(response, "<li>Pipelines</li>")

    def test_empty_facts_are_hidden(self):
        SiteSettings.objects.filter(pk=1).update(
            about_location="", time_zone="", email="", github_url="", linkedin_url=""
        )
        Language.objects.all().delete()
        response = self.client.get(ABOUT)
        self.assertNotContains(response, 'aria-label="Quick facts"')
        self.assertNotContains(response, "languages-heading")
        self.assertNotContains(response, "data-clock")
        self.assertNotContains(response, "js/clock.js")

    def test_service_description_renders_formatting(self):
        Service.objects.create(title="Bots", description="Bots that *really* work.")
        self.assertContains(self.client.get(ABOUT), "<em>really</em>")


class QuickFactsAdminTests(AdminLoginMixin, TestCase):
    url = f"{ADMIN}portfolio/sitesettings/1/change/"

    def test_page_has_facts_languages_and_toolbar(self):
        SiteSettings.load()
        page = self.client.get(self.url)
        self.assertContains(page, "Quick facts (About page)")
        self.assertContains(page, "Languages (About page)")
        self.assertContains(page, '<option value="America/Sao_Paulo">')
        self.assertContains(page, "data-markdown")
        self.assertContains(page, "portfolio_admin/markdown_toolbar.js")

    def test_long_text_boxes_get_the_toolbar(self):
        for model in ["project", "experience", "service"]:
            with self.subTest(model=model):
                page = self.client.get(f"{ADMIN}portfolio/{model}/add/")
                self.assertContains(page, "data-markdown")


class SeedQuickFactsTests(TempMediaMixin, TestCase):
    def test_seed_fills_facts_and_languages_once(self):
        call_command("seed_demo", stdout=io.StringIO())
        call_command("seed_demo", stdout=io.StringIO())
        site = SiteSettings.load()
        self.assertEqual(site.time_zone, "America/Sao_Paulo")
        self.assertEqual(site.about_location, "Curitiba, Brazil")
        self.assertEqual(site.languages.count(), 2)
