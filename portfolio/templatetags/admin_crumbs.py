from django import template
from django.urls import Resolver404, resolve

register = template.Library()


def _is_app_page(link):
    # Django's per-app pages ("Portfolio administration") redirect home, so their crumb is noise.
    try:
        return bool(link) and resolve(link).url_name == "app_list"
    except Resolver404:
        return False


@register.filter
def clean_crumbs(parts):
    """Unfold's breadcrumb parts without app crumbs and without a repeat of the crumb before."""
    cleaned = []
    for part in parts:
        if _is_app_page(part.get("link")):
            continue
        if cleaned and str(cleaned[-1]["title"]) == str(part["title"]):
            continue
        cleaned.append(part)
    return cleaned
