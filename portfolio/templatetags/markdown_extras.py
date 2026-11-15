"""
{{ text|markdown }}: turns the simple Markdown typed in the admin into HTML.

Before Markdown runs, the text is tidied so it behaves the way it looks in the box:
- lines starting with "·" or "•" become list items, like "- " does;
- spaces at the start of a line are ignored (in Markdown they would turn the
  line into a grey code block, which is never what was meant here);
- a list right after a line of text still becomes a list (Markdown wants a
  blank line before it);
- every Enter is a line break, a blank line starts a new paragraph.

The result is cleaned with nh3 so only basic formatting tags survive.
Even though only the admin writes these texts, a pasted <script> or
<iframe> should never reach the public page.
"""

import re

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

DOT_BULLET = re.compile(r"^[·•]\s+")
LIST_ITEM = re.compile(r"^([-*+]|\d+[.)])\s+")
# Page titles (h1/h2) already exist on every page, so "#" and "##" become h3.
BIG_HEADING = re.compile(r"<(/?)h[12]>")
SMALL_HEADING = re.compile(r"<(/?)h[56]>")


def tidy(text):
    """Prepare admin text for Markdown. Code fenced with ``` is left untouched."""
    lines = []
    in_fence = False
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip() if not in_fence else raw
        if line.startswith("```"):
            in_fence = not in_fence
            lines.append(line)
            continue
        if not in_fence:
            line = DOT_BULLET.sub("- ", line)
            starts_list = bool(LIST_ITEM.match(line))
            previous = lines[-1] if lines else ""
            if starts_list and previous and not LIST_ITEM.match(previous):
                lines.append("")
        lines.append(line)
    return "\n".join(lines)


@register.filter(name="markdown")
def markdown_filter(text):
    if not text:
        return ""
    html = md.markdown(tidy(text), extensions=["sane_lists", "nl2br", "fenced_code"])
    html = BIG_HEADING.sub(r"<\1h3>", html)
    html = SMALL_HEADING.sub(r"<\1h4>", html)
    clean = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer",
    )
    return mark_safe(clean)
