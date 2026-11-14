from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase

from portfolio.models import Project, Service, SiteSettings
from portfolio.validators import (
    RandomFilename,
    validate_file_size,
    validate_image_extension,
    validate_pdf_extension,
)

from .helpers import TempMediaMixin, make_png


class SiteSettingsTests(TestCase):
    def test_load_creates_one_row(self):
        SiteSettings.load()
        SiteSettings.load()
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_a_second_object_overwrites_the_single_row(self):
        first = SiteSettings.load()
        SiteSettings(site_name="New", headline="h").save()
        self.assertEqual(SiteSettings.objects.count(), 1)
        settings = SiteSettings.load()
        self.assertEqual(settings.site_name, "New")
        self.assertEqual(settings.created_at, first.created_at)


class ProjectTests(TempMediaMixin, TestCase):
    def make_project(self, title, **extra):
        return Project.objects.create(
            title=title, pitch="p", what_it_does="w", cover_image=make_png(), **extra
        )

    def test_slug_is_filled_from_title(self):
        self.assertEqual(self.make_project("Match Replay System").slug, "match-replay-system")

    def test_absolute_url(self):
        self.assertEqual(self.make_project("ParkEye").get_absolute_url(), "/projects/parkeye/")

    def test_published_only_and_in_admin_order(self):
        self.make_project("B", order=2)
        self.make_project("A", order=1)
        self.make_project("Hidden", order=0, is_published=False)
        titles = list(Project.objects.published().values_list("title", flat=True))
        self.assertEqual(titles, ["A", "B"])

    def test_uploads_get_random_names(self):
        project = self.make_project("ParkEye")
        self.assertRegex(project.cover_image.name, r"^projects/[0-9a-f]{32}\.png$")


class PublishedFilterTests(TestCase):
    def test_service_published(self):
        Service.objects.create(title="On", description="d")
        Service.objects.create(title="Off", description="d", is_published=False)
        self.assertEqual([s.title for s in Service.objects.published()], ["On"])


class ValidatorTests(SimpleTestCase):
    def test_file_over_5mb_is_rejected(self):
        big = SimpleUploadedFile("a.png", b"0" * (5 * 1024 * 1024 + 1))
        with self.assertRaisesMessage(ValidationError, "The maximum is 5 MB"):
            validate_file_size(big)

    def test_file_of_5mb_is_accepted(self):
        validate_file_size(SimpleUploadedFile("a.png", b"0" * (5 * 1024 * 1024)))

    def test_image_extensions(self):
        for name in ["a.jpg", "a.jpeg", "a.PNG", "a.webp"]:
            validate_image_extension(SimpleUploadedFile(name, b"x"))
        for name in ["a.exe", "a.gif", "a.svg"]:
            with self.assertRaises(ValidationError):
                validate_image_extension(SimpleUploadedFile(name, b"x"))

    def test_pdf_extension(self):
        validate_pdf_extension(SimpleUploadedFile("cv.pdf", b"x"))
        with self.assertRaisesMessage(ValidationError, "Only PDF files are allowed."):
            validate_pdf_extension(SimpleUploadedFile("cv.docx", b"x"))

    def test_random_filename_keeps_lowercase_extension(self):
        path = RandomFilename("logos")(None, "My Logo.PNG")
        self.assertRegex(path, r"^logos/[0-9a-f]{32}\.png$")
