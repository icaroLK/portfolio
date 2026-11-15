"""
{% seo_tags %}: the <title>, description, canonical, Open Graph and Twitter tags.

Each page template passes only what differs from the Site settings defaults:

    {% block seo %}{% seo_tags title=project.title description=project.pitch image=project.cover_image %}{% endblock %}
"""

from django import template

from portfolio.thumbnails import thumbnail

register = template.Library()


@register.inclusion_tag("partials/seo.html", takes_context=True)
def seo_tags(context, title="", description="", image=None, og_type="website", noindex=False):
    request = context["request"]
    site = context["site"]
    site_name = site.site_name

    # A 1200 px JPEG copy: light enough for WhatsApp, a format every app shows.
    share_image = thumbnail(image or site.og_image, "share")

    return {
        "title": f"{title} · {site_name}" if title else site_name,
        "description": description or site.meta_description,
        # The canonical address drops ?type=... so filtered views do not compete in Google.
        "canonical_url": request.build_absolute_uri(request.path),
        "site_name": site_name,
        "og_type": og_type,
        # Share previews need the full address, not "/media/...".
        "image_url": request.build_absolute_uri(share_image.url) if share_image else "",
        "image": share_image,
        "image_alt": title or site_name,
        "noindex": noindex,
    }
