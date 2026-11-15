"""Header, footer and styleguide (Sprint 2)."""

import re

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from portfolio.models import SiteSettings

from .helpers import TempMediaMixin


def make_settings(**overrides):
    values = {
        "site_name": "Test Name",
        "headline": "Test headline",
        "email": "me@example.com",
        "github_url": "https://github.com/someone",
        "linkedin_url": "https://www.linkedin.com/in/someone",
        "location_line": "Test City · Remote",
    }
    values.update(overrides)
    return SiteSettings.objects.create(**values)


class HeaderTests(TestCase):
    def setUp(self):
        make_settings()

    def test_site_name_links_home(self):
        response = self.client.get("/")
        self.assertContains(response, "Test Name")
        self.assertContains(response, 'href="/"')

    def test_nav_links_present(self):
        response = self.client.get("/")
        self.assertContains(response, 'href="/about/"')
        self.assertContains(response, 'href="/about/#contact"')

    def test_projects_link_active_on_home(self):
        response = self.client.get("/")
        # Both the desktop and the mobile "Projects" link are marked as the current page.
        self.assertContains(response, 'aria-current="page">Projects</a>', count=2)

    def test_mobile_menu_button(self):
        response = self.client.get("/")
        self.assertContains(response, 'aria-label="Open menu"')
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, 'aria-controls="mobile-menu"')
        self.assertContains(response, 'id="mobile-menu"')
        self.assertContains(response, "js/menu.js")

    def test_resume_hidden_without_pdf(self):
        response = self.client.get("/")
        self.assertNotContains(response, ">Resume<")


class ResumeLinkTests(TempMediaMixin, TestCase):
    def test_resume_links_appear_with_pdf(self):
        pdf = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        make_settings(resume_pdf=pdf)
        response = self.client.get("/")
        # Desktop pill, mobile panel and footer, all through the stable /resume/ link.
        self.assertContains(response, 'href="/resume/"', count=3)


class FooterTests(TestCase):
    def test_footer_uses_site_settings(self):
        make_settings()
        response = self.client.get("/")
        self.assertContains(response, "&copy; Test Name · Test City · Remote")
        self.assertContains(response, 'href="mailto:me@example.com"')
        self.assertContains(response, 'href="https://github.com/someone"')
        self.assertContains(response, 'href="https://www.linkedin.com/in/someone"')

    def test_empty_links_are_hidden(self):
        make_settings(email="", github_url="", linkedin_url="")
        response = self.client.get("/")
        self.assertNotContains(response, "mailto:")
        self.assertNotContains(response, ">GitHub<")
        self.assertNotContains(response, ">LinkedIn<")

    def test_editing_settings_changes_footer(self):
        settings = make_settings()
        settings.github_url = "https://github.com/changed"
        settings.save()
        response = self.client.get("/")
        self.assertContains(response, 'href="https://github.com/changed"')
        self.assertNotContains(response, "github.com/someone")

    def test_settings_loaded_in_one_query(self):
        make_settings()
        with CaptureQueriesContext(connection) as queries:
            self.client.get("/")
        # The page runs its own project queries; header and footer share one settings query.
        settings_queries = [q for q in queries if "portfolio_sitesettings" in q["sql"]]
        self.assertEqual(len(settings_queries), 1)


class StyleguideTests(TestCase):
    def test_hidden_when_debug_off(self):
        # Tests always run with DEBUG off, like production.
        self.assertEqual(self.client.get(reverse("portfolio:styleguide")).status_code, 404)

    @override_settings(DEBUG=True)
    def test_shows_every_component_when_debug_on(self):
        make_settings(status_badge_text="Badge text here")
        response = self.client.get(reverse("portfolio:styleguide"))
        self.assertEqual(response.status_code, 200)
        for text in [
            "Colors",
            "Typography",
            "Buttons",
            "Chips and tags",
            "Eyebrow and section heading",
            "Card shells",
            "Status badge",
            "Badge text here",
            "btn-primary",
            "btn-secondary",
            "card-lg",
        ]:
            self.assertContains(response, text)

    @override_settings(DEBUG=True)
    def test_shows_seed_data_in_chips(self):
        from django.core.management import call_command

        from portfolio.models import ProjectTech, Skill

        call_command("seed_demo", verbosity=0)
        response = self.client.get(reverse("portfolio:styleguide"))
        self.assertContains(response, ProjectTech.objects.first().purpose)
        self.assertContains(response, Skill.objects.first().name)


class NoSidewaysScrollTests(TestCase):
    """Guard against fixed widths wider than a 390 px phone in shared layout."""

    def test_layout_has_no_wide_fixed_widths(self):
        make_settings()
        html = self.client.get("/").content.decode()
        self.assertNotIn("w-screen", html)
        self.assertNotIn("min-w-[", html)
        # A fixed width of 400 px or more breaks a phone. max-w-[...] is fine: it only caps.
        self.assertIsNone(re.search(r"(?<![\w-])w-\[[4-9]\d\d", html))
