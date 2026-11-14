"""
Values every template can use without each view passing them.

Registered in TEMPLATES in config/settings/base.py.
"""

from django.utils.functional import SimpleLazyObject

from .models import SiteSettings

# Which header link is "active" for each page (by URL name).
NAV_SECTIONS = {
    "home": "projects",
    "project_detail": "projects",
    "about": "about",
}


def site(request):
    match = getattr(request, "resolver_match", None)
    return {
        # Lazy: the database is only queried if a template actually uses `site`.
        "site": SimpleLazyObject(SiteSettings.load),
        "nav_section": NAV_SECTIONS.get(match.url_name if match else None, ""),
    }
