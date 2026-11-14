"""
Custom admin site: shows the site name from Site settings in the admin header
instead of "Django administration".
"""

from django.apps import apps
from django.contrib import admin
from django.contrib.admin.apps import AdminConfig


class PortfolioAdminSite(admin.AdminSite):
    index_title = "Content"

    def each_context(self, request):
        context = super().each_context(request)
        SiteSettings = apps.get_model("portfolio", "SiteSettings")
        settings = SiteSettings.objects.filter(pk=1).only("site_name").first()
        name = settings.site_name if settings and settings.site_name else "Site"
        context["site_header"] = f"{name} admin"
        context["site_title"] = f"{name} admin"
        return context


class PortfolioAdminConfig(AdminConfig):
    """Replaces django.contrib.admin in INSTALLED_APPS so admin.site is our class."""

    default_site = "config.admin.PortfolioAdminSite"
