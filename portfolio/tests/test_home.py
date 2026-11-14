from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from portfolio.models import Project, ProjectTech, SiteSettings, Tech, TypeTag

from .helpers import TempMediaMixin, make_png


class HomeTestData(TempMediaMixin, TestCase):
    """Two featured, two archive and one unpublished project, with tags and stack."""

    @classmethod
    def setUpTestData(cls):
        SiteSettings.objects.create(
            site_name="Test Name",
            headline="Test headline",
            subheadline="Test subheadline",
            status_badge_text="Open to work",
            show_status_badge=True,
        )
        cls.bot = TypeTag.objects.create(name="Bot", slug="bot", order=0)
        cls.website = TypeTag.objects.create(name="Website", slug="website", order=1)
        cls.vision = TypeTag.objects.create(name="Vision", slug="vision", order=2)
        cls.hidden_tag = TypeTag.objects.create(name="Hidden", slug="hidden", order=3)

        cls.feat_a = cls.make("Feat A", order=0, featured=True, tags=[cls.vision])
        cls.feat_b = cls.make("Feat B", order=1, featured=True)
        cls.arch_a = cls.make("Arch A", order=2, tags=[cls.bot])
        cls.arch_b = cls.make("Arch B", order=3, tags=[cls.website, cls.bot])
        cls.draft = cls.make("Draft", order=4, published=False, tags=[cls.hidden_tag])

        techs = [Tech.objects.create(name=f"Tech{i}", slug=f"tech{i}") for i in range(5)]
        for i, tech in enumerate(techs):
            ProjectTech.objects.create(project=cls.feat_a, tech=tech, purpose="x", order=i)
            ProjectTech.objects.create(project=cls.arch_a, tech=tech, purpose="x", order=i)

    @classmethod
    def make(cls, title, order, featured=False, published=True, tags=()):
        project = Project.objects.create(
            title=title,
            pitch=f"{title} pitch",
            what_it_does="Text",
            cover_image=make_png(),
            order=order,
            is_featured=featured,
            is_published=published,
        )
        project.type_tags.set(tags)
        return project

    def get(self, **params):
        return self.client.get(reverse("portfolio:home"), params)

    def titles(self, response, key):
        return [p.title for p in response.context[key]]


class HomeHeroTests(HomeTestData):
    def test_hero_comes_from_site_settings(self):
        response = self.get()
        self.assertContains(response, "Test headline")
        self.assertContains(response, "Test subheadline")
        self.assertContains(response, "Open to work")
        self.assertContains(response, 'href="#featured"')
        self.assertContains(response, 'href="/about/#contact"')

    def test_badge_toggle_hides_the_badge(self):
        SiteSettings.objects.filter(pk=1).update(show_status_badge=False)
        self.assertNotContains(self.get(), "Open to work")


class HomeSectionsTests(HomeTestData):
    def test_featured_and_archive_split_in_admin_order(self):
        response = self.get()
        self.assertEqual(self.titles(response, "featured_projects"), ["Feat A", "Feat B"])
        self.assertEqual(self.titles(response, "archive_projects"), ["Arch A", "Arch B"])

    def test_unpublished_project_is_not_shown(self):
        self.assertNotContains(self.get(), "Draft")

    def test_toggling_featured_moves_the_project(self):
        Project.objects.filter(pk=self.arch_a.pk).update(is_featured=True)
        response = self.get()
        self.assertIn("Arch A", self.titles(response, "featured_projects"))
        self.assertNotIn("Arch A", self.titles(response, "archive_projects"))

    def test_reordering_changes_the_page_order(self):
        Project.objects.filter(pk=self.arch_b.pk).update(order=0)
        self.assertEqual(self.titles(self.get(), "archive_projects"), ["Arch B", "Arch A"])

    def test_featured_section_hidden_when_nothing_is_featured(self):
        Project.objects.update(is_featured=False)
        response = self.get()
        self.assertNotContains(response, "Featured projects")
        self.assertContains(response, 'href="#more-projects"')

    def test_cards_link_to_the_project_page(self):
        self.assertContains(self.get(), 'href="/projects/arch-a/"')

    def test_cards_show_only_the_first_three_stack_items(self):
        response = self.get()
        self.assertContains(response, "Tech2")
        self.assertNotContains(response, "Tech3")

    def test_query_count_does_not_grow_with_projects(self):
        self.get()  # warm up anything cached once per process
        with CaptureQueriesContext(connection) as first:
            self.get()
        for i in range(5):
            project = self.make(f"Extra {i}", order=10 + i, tags=[self.bot])
            ProjectTech.objects.create(
                project=project, tech=Tech.objects.first(), purpose="x", order=0
            )
        with self.assertNumQueries(len(first.captured_queries)):
            self.get()


class HomeFilterTests(HomeTestData):
    def test_filter_buttons_only_for_tags_with_archive_projects(self):
        names = [t.name for t in self.get().context["filter_tags"]]
        # Vision is only on a featured project, Hidden only on an unpublished one.
        self.assertEqual(names, ["Bot", "Website"])

    def test_each_filter_shows_only_its_projects(self):
        self.assertEqual(self.titles(self.get(type="bot"), "archive_projects"), ["Arch A", "Arch B"])
        self.assertEqual(self.titles(self.get(type="website"), "archive_projects"), ["Arch B"])

    def test_filter_does_not_touch_featured(self):
        response = self.get(type="website")
        self.assertEqual(self.titles(response, "featured_projects"), ["Feat A", "Feat B"])

    def test_active_filter_is_marked(self):
        response = self.get(type="website")
        self.assertContains(response, 'href="/?type=website#more-projects"')
        self.assertContains(response, 'aria-current="page">Website</a>', html=False)

    def test_unknown_filter_shows_empty_state(self):
        response = self.get(type="nope")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No projects of this type yet.")

    def test_no_empty_state_when_projects_match(self):
        self.assertNotContains(self.get(type="bot"), "No projects of this type yet.")
