"""
{% thumbnail image "card" as thumb %} gives thumb.url, thumb.width and thumb.height.

Sizes are listed in portfolio/thumbnails.py.
"""

from django import template

from portfolio.thumbnails import thumbnail as make_thumbnail

register = template.Library()


@register.simple_tag
def thumbnail(image, size):
    return make_thumbnail(image, size)
