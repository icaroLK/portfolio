"""
{{ text|markdown }}: turns the simple Markdown typed in the admin into HTML.

The result is cleaned with nh3 so only basic formatting tags survive.
Even though only the admin writes these texts, a pasted <script> or
<iframe> should never reach the public page.
"""

import markdown as md
import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = {
    "p", "br", "strong", "em", "code", "pre", "blockquote",
    "ul", "ol", "li", "h3", "h4", "a", "hr",
}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}


@register.filter(name="markdown")
def markdown_filter(text):
    if not text:
        return ""
    html = md.markdown(text, extensions=["sane_lists"])
    clean = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer",
    )
    return mark_safe(clean)
