from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from portfolio.models import SiteSettings

from .helpers import TempMediaMixin
from .test_project_detail import make_project


def make_pdf(name="resume.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4 test", content_type="application/pdf")


class ResumeTests(TempMediaMixin, TestCase):
    def test_no_resume_gives_404(self):
        SiteSettings.objects.create(site_name="N", headline="H")
        self.assertEqual(self.client.get("/resume/").status_code, 404)

    def test_redirects_to_the_current_pdf(self):
        site = SiteSettings.objects.create(site_name="N", headline="H", resume_pdf=make_pdf())
        response = self.client.get("/resume/")
        self.assertRedirects(response, site.resume_pdf.url, fetch_redirect_response=False)

        # Replacing the file in the admin changes where /resume/ points.
        old_url = site.resume_pdf.url
        site.resume_pdf = make_pdf("new.pdf")
        site.save()
        response = self.client.get("/resume/")
        self.assertNotEqual(response["Location"], old_url)
        self.assertEqual(response["Location"], site.resume_pdf.url)

    def test_resume_buttons_use_the_stable_link(self):
        site = SiteSettings.objects.create(site_name="N", headline="H", resume_pdf=make_pdf())
        html = self.client.get("/about/").content.decode()
        self.assertNotIn(site.resume_pdf.url, html)
        # Header (desktop and mobile), footer and the About button.
        self.assertEqual(html.count('href="/resume/"'), 4)


class SitemapTests(TempMediaMixin, TestCase):
    def test_lists_pages_and_published_projects_only(self):
        make_project("Shown", order=0)
        make_project("Hidden", order=1, published=False)
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("<loc>http://testserver/</loc>", body)
        self.assertIn("<loc>http://testserver/about/</loc>", body)
        self.assertIn("/projects/shown/", body)
        self.assertNotIn("/projects/hidden/", body)


class RobotsAndHealthTests(TestCase):
    def test_robots_allows_all_and_links_the_sitemap(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        body = response.content.decode()
        self.assertIn("Allow: /", body)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", body)
        # robots.txt is public: it must never reveal the secret admin path.
        self.assertNotIn(settings.ADMIN_PATH, body)

    def test_admin_pages_are_not_indexed(self):
        response = self.client.get(f"/{settings.ADMIN_PATH}/login/")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertNotIn("X-Robots-Tag", self.client.get("/robots.txt"))

    def test_healthz_says_ok_without_queries(self):
        with self.assertNumQueries(0):
            response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")
