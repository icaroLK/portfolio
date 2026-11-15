from html.parser import HTMLParser

from django.test import RequestFactory, TestCase, override_settings
from django.views.defaults import server_error

from portfolio.models import SiteSettings

from .helpers import TempMediaMixin, make_png
from .test_project_detail import make_project


class ImageAltCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images_without_alt = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img" and "alt" not in attrs:
            self.images_without_alt.append(attrs.get("src"))


class AccessibilityTests(TempMediaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteSettings.objects.create(site_name="N", headline="H", profile_photo=make_png())
        cls.project = make_project("Shown", order=0)
        cls.project.gallery.create(image=make_png(), order=0)

    def test_skip_link_jumps_to_main(self):
        html = self.client.get("/").content.decode()
        self.assertIn('href="#main"', html)
        self.assertIn('<main id="main"', html)
        # The skip link is the first focusable thing on the page.
        self.assertLess(html.index("Skip to content"), html.index("<header"))

    def test_every_image_has_alt_text(self):
        for url in ["/", "/about/", self.project.get_absolute_url()]:
            collector = ImageAltCollector()
            collector.feed(self.client.get(url).content.decode())
            self.assertEqual(collector.images_without_alt, [], url)

    def test_cover_alt_defaults_to_project_title(self):
        self.assertContains(self.client.get("/"), 'alt="Shown"')


class ServerErrorPageTests(TestCase):
    def test_500_page_needs_no_database(self):
        request = RequestFactory().get("/")
        with self.assertNumQueries(0):
            response = server_error(request)
        self.assertEqual(response.status_code, 500)
        html = response.content.decode()
        self.assertIn("Something went wrong.", html)
        self.assertIn("css/site.css", html)
        self.assertIn('<meta name="robots" content="noindex">', html)

    @override_settings(DEBUG=True)
    def test_500_preview_works_in_debug(self):
        self.assertEqual(self.client.get("/styleguide/500/").status_code, 500)

    def test_500_preview_is_hidden_without_debug(self):
        self.assertEqual(self.client.get("/styleguide/500/").status_code, 404)
