"""Pages listed in /sitemap.xml: Home, About and every published project."""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Project


class StaticPagesSitemap(Sitemap):
    def items(self):
        return ["portfolio:home", "portfolio:about"]

    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    def items(self):
        return Project.objects.published()

    def lastmod(self, project):
        return project.updated_at


SITEMAPS = {"pages": StaticPagesSitemap, "projects": ProjectSitemap}
