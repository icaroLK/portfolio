from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from portfolio.models import (
    Project,
    ProjectFeature,
    ProjectImage,
    ProjectTech,
    SiteSettings,
    Tech,
    TypeTag,
)
from portfolio.templatetags.markdown_extras import markdown_filter

from .helpers import TempMediaMixin, make_png


def make_project(title, order, published=True, **fields):
    return Project.objects.create(
        title=title,
        pitch=f"{title} pitch",
        what_it_does=f"{title} does things.",
        cover_image=make_png(),
        order=order,
        is_published=published,
        **fields,
    )


class ProjectDetailTestData(TempMediaMixin, TestCase):
    """A fully filled project, a minimal one, and an unpublished one."""

    @classmethod
    def setUpTestData(cls):
        SiteSettings.objects.create(site_name="Test Name", headline="H")
        cls.full = make_project(
            "Full",
            order=0,
            role="Solo project",
            period="Nov 2026",
            video_url="https://youtu.be/dQw4w9WgXcQ",
            live_url="https://live.example.com/",
            repo_url="https://github.com/example/full",
            how_it_works="Camera feeds go to a **worker**.\n\n- step one\n- step two",
            architecture_image=make_png("arch.png"),
        )
        cls.full.type_tags.set([
            TypeTag.objects.create(name="Computer Vision", slug="cv", order=0),
            TypeTag.objects.create(name="System", slug="system", order=1),
        ])
        for i in range(4):
            ProjectFeature.objects.create(project=cls.full, text=f"Feature {i + 1}", order=i)
        for i, name in enumerate(["Python", "OpenCV", "Django", "PostgreSQL", "Docker"]):
            tech = Tech.objects.create(name=name, slug=name.lower())
            ProjectTech.objects.create(project=cls.full, tech=tech, purpose=f"use {i}", order=i)
        for i in range(3):
            ProjectImage.objects.create(
                project=cls.full, image=make_png(f"g{i}.png"), caption=f"Shot {i}", order=i
            )

        cls.minimal = make_project("Minimal", order=1)
        cls.draft = make_project("Draft", order=2, published=False)

    def get(self, project):
        return self.client.get(reverse("portfolio:project_detail", args=[project.slug]))


class FullProjectTests(ProjectDetailTestData):
    def test_header_block(self):
        response = self.get(self.full)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Computer Vision · System")
        self.assertContains(response, "<h1", count=1)
        self.assertContains(response, "Full pitch")
        self.assertContains(response, "Solo project · Nov 2026")
        self.assertContains(response, "All projects")

    def test_buttons_open_in_new_tab(self):
        response = self.get(self.full)
        self.assertContains(
            response, 'href="https://live.example.com/" target="_blank" rel="noopener"'
        )
        self.assertContains(
            response, 'href="https://github.com/example/full" target="_blank" rel="noopener"'
        )

    def test_video_is_embedded(self):
        self.assertContains(
            self.get(self.full), 'src="https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"'
        )

    def test_loom_video_is_embedded(self):
        Project.objects.filter(pk=self.full.pk).update(
            video_url="https://www.loom.com/share/abc123def456"
        )
        self.assertContains(self.get(self.full), 'src="https://www.loom.com/embed/abc123def456"')

    def test_features_are_numbered_in_order(self):
        content = self.get(self.full).content.decode()
        for number in ["01", "02", "03", "04"]:
            self.assertIn(f">{number}</span>", content)
        self.assertLess(content.index("Feature 1"), content.index("Feature 4"))

    def test_stack_chips_show_tech_and_purpose(self):
        response = self.get(self.full)
        self.assertContains(response, "OpenCV")
        self.assertContains(response, "use 1")

    def test_how_it_works_renders_markdown_and_image(self):
        response = self.get(self.full)
        self.assertContains(response, "For technical readers")
        self.assertContains(response, "<strong>worker</strong>")
        self.assertContains(response, "<li>step one</li>")
        self.assertContains(response, self.full.architecture_image.url)

    def test_gallery_opens_in_the_viewer(self):
        response = self.get(self.full)
        for image in self.full.gallery.all():
            self.assertContains(response, f'href="{image.image.url}" data-gallery-item')
        self.assertContains(response, 'alt="Shot 0"')
        self.assertContains(response, "<dialog data-lightbox")
        self.assertContains(response, 'aria-label="Close"')
        self.assertContains(response, 'aria-label="Next image"')
        self.assertContains(response, "js/gallery.js")

    def test_page_title(self):
        self.assertContains(self.get(self.full), "<title>Full · Test Name</title>")

    def test_query_count_is_fixed(self):
        # Warm the lazy site settings so only the page's own queries are counted.
        self.get(self.full)
        with CaptureQueriesContext(connection) as queries:
            self.get(self.full)
        self.assertLessEqual(len(queries), 10)


class MinimalProjectTests(ProjectDetailTestData):
    """Only title, pitch, cover and what_it_does: no empty sections or broken buttons."""

    def test_optional_sections_are_hidden(self):
        response = self.get(self.minimal)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What it does")
        self.assertContains(response, "Minimal does things.")
        for text in [
            "<iframe",
            "Live demo",
            "GitHub",
            "Key features",
            "Tech stack",
            "How it works",
            "Gallery",
            "<dialog",
            "gallery.js",
            'target="_blank"',
        ]:
            with self.subTest(text=text):
                self.assertNotContains(response, text)


class NextProjectTests(ProjectDetailTestData):
    def test_next_project_follows_admin_order(self):
        self.assertEqual(self.full.next_project(), self.minimal)
        self.assertContains(self.get(self.full), 'href="/projects/minimal/"')

    def test_last_project_wraps_to_first(self):
        self.assertEqual(self.minimal.next_project(), self.full)
        self.assertContains(self.get(self.minimal), 'href="/projects/full/"')

    def test_unpublished_projects_are_skipped(self):
        Project.objects.filter(pk=self.draft.pk).update(order=1)
        Project.objects.filter(pk=self.minimal.pk).update(order=5)
        self.minimal.refresh_from_db()
        self.assertEqual(self.full.next_project(), self.minimal)

    def test_ties_in_order_still_move_forward(self):
        Project.objects.filter(pk=self.minimal.pk).update(order=0)
        self.minimal.refresh_from_db()
        self.assertEqual(self.full.next_project(), self.minimal)
        self.assertEqual(self.minimal.next_project(), self.full)

    def test_only_one_published_project_hides_the_card(self):
        Project.objects.filter(pk=self.minimal.pk).update(is_published=False)
        self.assertIsNone(self.full.next_project())
        self.assertNotContains(self.get(self.full), "Next project")


@override_settings(DEBUG=False)
class NotFoundTests(ProjectDetailTestData):
    def test_unpublished_project_shows_styled_404(self):
        response = self.get(self.draft)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "Page not found.", status_code=404)

    def test_missing_slug_shows_styled_404(self):
        response = self.client.get("/projects/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_404_preview_is_hidden_without_debug(self):
        response = self.client.get(reverse("portfolio:preview_404"))
        self.assertEqual(response.status_code, 404)


class NotFoundPreviewTests(TestCase):
    @override_settings(DEBUG=True)
    def test_preview_shows_styled_page(self):
        response = self.client.get(reverse("portfolio:preview_404"))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found.", status_code=404)


class VideoUrlAdminCheckTests(TempMediaMixin, TestCase):
    def test_non_youtube_or_loom_link_is_rejected(self):
        project = make_project("P", order=0, video_url="https://vimeo.com/1")
        with self.assertRaises(ValidationError) as caught:
            project.full_clean()
        self.assertIn("video_url", caught.exception.message_dict)


class MarkdownFilterTests(TestCase):
    def test_basic_formatting(self):
        html = markdown_filter("Hello **bold** and `code`")
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("<code>code</code>", html)

    def test_unsafe_html_is_removed(self):
        html = markdown_filter('<script>alert(1)</script><iframe src="x"></iframe>[a](javascript:alert(1))')
        self.assertNotIn("<script", html)
        self.assertNotIn("<iframe", html)
        self.assertNotIn("javascript:", html)

    def test_links_get_safe_rel(self):
        self.assertIn('rel="noopener noreferrer"', markdown_filter("[site](https://example.com)"))

    def test_empty_text(self):
        self.assertEqual(markdown_filter(""), "")
