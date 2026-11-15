import io

from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from portfolio.models import SiteSettings
from portfolio.thumbnails import thumbnail

from .helpers import TempMediaMixin, make_png
from .test_project_detail import make_project


def make_transparent_png(size=(800, 400)):
    buffer = io.BytesIO()
    Image.new("RGBA", size, (255, 0, 0, 0)).save(buffer, "PNG")
    return SimpleUploadedFile("logo.png", buffer.getvalue(), content_type="image/png")


class ThumbnailTests(TempMediaMixin, TestCase):
    def setUp(self):
        cache.clear()

    def test_resizes_to_webp_and_keeps_proportions(self):
        project = make_project("Big", order=0, cover_image=make_png(size=(2000, 1000)))
        thumb = thumbnail(project.cover_image, "card")
        self.assertTrue(thumb.url.endswith(".webp"))
        self.assertEqual((thumb.width, thumb.height), (640, 320))
        with default_storage.open(thumb.url.removeprefix("/media/")) as stored:
            picture = Image.open(stored)
            self.assertEqual(picture.format, "WEBP")
            self.assertEqual(picture.size, (640, 320))

    def test_never_enlarges_small_images(self):
        project = make_project("Small", order=0, cover_image=make_png(size=(300, 200)))
        thumb = thumbnail(project.cover_image, "featured")
        self.assertEqual((thumb.width, thumb.height), (300, 200))

    def test_reuses_the_saved_file(self):
        project = make_project("Again", order=0, cover_image=make_png(size=(1000, 500)))
        first = thumbnail(project.cover_image, "card")
        cache.clear()  # forces a read from disk instead of the cache
        second = thumbnail(project.cover_image, "card")
        self.assertEqual(first, second)

    def test_share_copy_is_jpeg_on_white(self):
        site = SiteSettings.objects.create(site_name="N", headline="H", og_image=make_transparent_png())
        thumb = thumbnail(site.og_image, "share")
        self.assertTrue(thumb.url.endswith(".jpg"))
        with default_storage.open(thumb.url.removeprefix("/media/")) as stored:
            picture = Image.open(stored)
            self.assertEqual(picture.format, "JPEG")
            self.assertEqual(picture.getpixel((5, 5)), (255, 255, 255))

    def test_no_image_gives_none(self):
        site = SiteSettings.objects.create(site_name="N", headline="H")
        self.assertIsNone(thumbnail(site.profile_photo, "avatar"))

    def test_unreadable_image_falls_back_to_the_original(self):
        project = make_project("Broken", order=0)
        default_storage.delete(project.cover_image.name)
        thumb = thumbnail(project.cover_image, "card")
        self.assertEqual(thumb.url, project.cover_image.url)
        self.assertEqual(thumb.size_attrs, "")

    def test_pages_use_thumbnails_not_originals(self):
        SiteSettings.objects.create(site_name="N", headline="H")
        project = make_project("Shown", order=0, cover_image=make_png(size=(1000, 600)))
        html = self.client.get("/").content.decode()
        self.assertIn("/media/thumbs/card/", html)
        self.assertNotIn(f'src="{project.cover_image.url}"', html)
        self.assertIn('width="640" height="384"', html)
