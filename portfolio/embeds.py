"""
Turns a YouTube or Loom page link into the URL an <iframe> can play.

People paste the link they see in the address bar or the share button
(for example youtube.com/watch?v=abc or loom.com/share/abc). Those pages
refuse to load inside an iframe, so we rewrite them to the embed form.
"""

import re
from urllib.parse import parse_qs, urlparse

from django.core.exceptions import ValidationError

YOUTUBE_HOSTS = {"youtube.com", "m.youtube.com", "youtube-nocookie.com"}
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
LOOM_ID = re.compile(r"^[A-Za-z0-9]+$")

# Path prefixes on youtube.com that are followed by the video id.
YOUTUBE_ID_PATHS = ("shorts", "embed", "live")


def _host(parsed):
    host = (parsed.hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _youtube_id(parsed):
    host = _host(parsed)
    parts = [p for p in parsed.path.split("/") if p]
    if host == "youtu.be" and parts:
        candidate = parts[0]
    elif host in YOUTUBE_HOSTS and parsed.path == "/watch":
        candidate = parse_qs(parsed.query).get("v", [""])[0]
    elif host in YOUTUBE_HOSTS and len(parts) >= 2 and parts[0] in YOUTUBE_ID_PATHS:
        candidate = parts[1]
    else:
        return None
    return candidate if YOUTUBE_ID.match(candidate) else None


def _loom_id(parsed):
    parts = [p for p in parsed.path.split("/") if p]
    if _host(parsed) == "loom.com" and len(parts) >= 2 and parts[0] in ("share", "embed"):
        return parts[1] if LOOM_ID.match(parts[1]) else None
    return None


def embed_url(url):
    """The iframe URL for a YouTube or Loom link, or None if it is neither."""
    if not url:
        return None
    parsed = urlparse(url.strip())
    if video_id := _youtube_id(parsed):
        # The no-cookie domain skips YouTube tracking cookies until the video is played.
        return f"https://www.youtube-nocookie.com/embed/{video_id}"
    if video_id := _loom_id(parsed):
        return f"https://www.loom.com/embed/{video_id}"
    return None


def validate_video_url(url):
    """Admin check: only links we know how to embed are accepted."""
    if url and embed_url(url) is None:
        raise ValidationError(
            "Use a YouTube link (youtube.com/watch?v=... or youtu.be/...) "
            "or a Loom link (loom.com/share/...)."
        )
