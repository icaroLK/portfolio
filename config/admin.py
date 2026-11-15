"""
Custom admin site, styled by django-unfold.

The header shows the site name from Site settings instead of "Django administration".
The functions below are called by Unfold (see UNFOLD in config/settings/base.py).
"""

from django.apps import apps
from django.contrib.admin.apps import AdminConfig
from django.shortcuts import redirect
from unfold.sites import UnfoldAdminSite


def site_name(request):
    """Name at the top of the sidebar (the Home link)."""
    SiteSettings = apps.get_model("portfolio", "SiteSettings")
    settings = SiteSettings.objects.filter(pk=1).only("site_name").first()
    return settings.site_name if settings and settings.site_name else "Site"


def admin_title(request):
    """Browser tab title."""
    return f"{site_name(request)} admin"


def unread_messages_badge(request):
    """Number next to "Inbox" in the sidebar. Nothing when there are no unread messages."""
    ContactMessage = apps.get_model("contact", "ContactMessage")
    return ContactMessage.objects.filter(is_read=False, is_spam=False).count() or None


class PortfolioAdminSite(UnfoldAdminSite):
    index_title = "Home"

    def app_index(self, request, app_label, extra_context=None):
        # Django's per-app pages ("Portfolio administration") duplicate the home
        # page and are not in the sidebar. Breadcrumbs link there, so send them home.
        return redirect("admin:index")


class PortfolioAdminConfig(AdminConfig):
    """Replaces django.contrib.admin in INSTALLED_APPS so admin.site is our class."""

    default_site = "config.admin.PortfolioAdminSite"
