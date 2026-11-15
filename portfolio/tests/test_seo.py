from django.test import TestCase, override_settings

from portfolio.models import SiteSettings

from .helpers import TempMediaMixin, make_png
from .test_project_detail import make_project


@override_settings(ALLOWED_HOSTS=["testserver"])
class SeoTagTests(TempMediaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteSettings.objects.create(
            site_name="Test Name",
            headline="H",
            meta_description="Default description.",
            og_image=make_png("share.png"),
        )
        cls.project = make_project("ParkEye", order=0)

    def test_home_uses_site_defaults(self):
        response = self.client.get("/?type=bots")
        self.assertContains(response, "<title>Test Name</title>", html=True)
        self.assertContains(response, '<meta name="description" content="Default description.">')
        # Canonical drops the filter query string.
        self.assertContains(response, '<link rel="canonical" href="http://testserver/">')
        self.assertContains(response, '<meta property="og:image" content="http://testserver/media/thumbs/share/site/')

    def test_about_has_its_own_title(self):
        response = self.client.get("/about/")
        self.assertContains(response, "<title>About · Test Name</title>", html=True)
        self.assertContains(response, '<link rel="canonical" href="http://testserver/about/">')

    def test_project_uses_pitch_and_cover_image(self):
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, "<title>ParkEye · Test Name</title>", html=True)
        self.assertContains(response, '<meta property="og:description" content="ParkEye pitch">')
        self.assertContains(response, '<meta property="og:type" content="article">')
        self.assertContains(response, '<meta property="og:image" content="http://testserver/media/thumbs/share/projects/')
        self.assertContains(response, '<meta name="twitter:card" content="summary_large_image">')

    def test_project_seo_description_wins_over_pitch(self):
        self.project.seo_description = "Custom SEO text."
        self.project.save()
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, '<meta name="description" content="Custom SEO text.">')
        self.assertNotContains(response, 'content="ParkEye pitch"')

    def test_one_title_and_one_h1_per_page(self):
        for url in ["/", "/about/", self.project.get_absolute_url()]:
            html = self.client.get(url).content.decode()
            self.assertEqual(html.count("<title>"), 1, url)
            self.assertEqual(html.count("<h1"), 1, url)

    @override_settings(DEBUG=False)
    def test_404_is_not_indexed(self):
        response = self.client.get("/missing-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, '<meta name="robots" content="noindex">', status_code=404)
        self.assertNotContains(response, 'rel="canonical"', status_code=404)
