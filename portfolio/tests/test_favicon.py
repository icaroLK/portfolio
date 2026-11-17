from django.core.cache import cache
from django.core.files.storage import default_storage
from django.test import TestCase
from PIL import Image

from portfolio.models import SiteSettings
from portfolio.thumbnails import thumbnail

from .helpers import TempMediaMixin, make_png


def open_stored(thumb):
    return Image.open(default_storage.open(thumb.url.removeprefix("/media/")))


class FaviconTests(TempMediaMixin, TestCase):
    def setUp(self):
        cache.clear()

    def test_tab_icon_is_a_round_64px_png(self):
        site = SiteSettings.objects.create(site_name="N", headline="H", profile_photo=make_png(size=(600, 400)))
        thumb = thumbnail(site.profile_photo, "favicon")
        self.assertTrue(thumb.url.endswith(".png"))
        with open_stored(thumb) as picture:
            self.assertEqual((picture.format, picture.size), ("PNG", (64, 64)))
            self.assertEqual(picture.getpixel((0, 0))[3], 0)  # corner is see-through
            self.assertEqual(picture.getpixel((32, 32))[3], 255)  # middle is solid

    def test_iphone_icon_is_a_solid_180px_square(self):
        site = SiteSettings.objects.create(site_name="N", headline="H", profile_photo=make_png(size=(100, 300)))
        with open_stored(thumbnail(site.profile_photo, "touch_icon")) as picture:
            self.assertEqual((picture.mode, picture.size), ("RGB", (180, 180)))

    def test_pages_link_the_icons_made_from_the_photo(self):
        site = SiteSettings.objects.create(site_name="N", headline="H", profile_photo=make_png(size=(400, 400)))
        html = self.client.get("/").content.decode()
        self.assertIn(f'rel="icon" type="image/png" sizes="64x64" href="{thumbnail(site.profile_photo, "favicon").url}"', html)
        self.assertIn(f'rel="apple-touch-icon" sizes="180x180" href="{thumbnail(site.profile_photo, "touch_icon").url}"', html)

    def test_new_photo_gives_a_new_icon_address(self):
        site = SiteSettings.objects.create(site_name="N", headline="H", profile_photo=make_png(size=(400, 400)))
        old = thumbnail(site.profile_photo, "favicon").url
        site.profile_photo = make_png(size=(400, 400))
        site.save()
        html = self.client.get("/").content.decode()
        self.assertNotIn(old, html)
        self.assertIn(thumbnail(site.profile_photo, "favicon").url, html)

    def test_no_photo_means_no_icon_tags(self):
        SiteSettings.objects.create(site_name="N", headline="H")
        html = self.client.get("/").content.decode()
        self.assertNotIn('rel="icon"', html)
        self.assertNotIn("apple-touch-icon", html)
