import io

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase

from portfolio.models import Experience, Project, SiteSettings

from .helpers import TempMediaMixin


def row_counts():
    return {m.__name__: m.objects.count() for m in apps.get_app_config("portfolio").get_models()}


class SeedDemoTests(TempMediaMixin, TestCase):
    def seed(self):
        call_command("seed_demo", stdout=io.StringIO())  # keep test output quiet

    def test_fills_the_expected_content(self):
        self.seed()
        counts = row_counts()
        self.assertEqual(counts["Project"], 4)
        self.assertEqual(counts["Experience"], 2)
        self.assertEqual(counts["Education"], 2)
        self.assertEqual(counts["SkillGroup"], 4)
        self.assertEqual(counts["Service"], 3)
        self.assertEqual(counts["SiteSettings"], 1)
        self.assertEqual(Project.objects.filter(is_featured=True).count(), 3)

    def test_running_twice_creates_no_duplicates(self):
        self.seed()
        first = row_counts()
        self.seed()
        self.assertEqual(row_counts(), first)

    def test_does_not_overwrite_admin_edits(self):
        self.seed()
        Project.objects.filter(slug="parkeye").update(pitch="My real pitch")
        settings = SiteSettings.load()
        settings.site_name = "Edited"
        settings.save()
        self.seed()
        self.assertEqual(Project.objects.get(slug="parkeye").pitch, "My real pitch")
        self.assertEqual(SiteSettings.load().site_name, "Edited")

    def test_empty_details_stays_empty(self):
        self.seed()
        self.assertEqual(Experience.objects.get(role="Freelance developer").details, "")
