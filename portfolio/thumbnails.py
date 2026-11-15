"""
Resized copies of uploaded images, so pages never send a 3000 px original.

A thumbnail is made the first time a page asks for it and saved next to the
uploads in media/thumbs/<size>/. Upload names are random, so a replaced image
gets a new name and its old thumbnail is simply no longer used.
"""

import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils.html import format_html
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Width in px and file format for each use. "share" is JPEG because some apps
# (older WhatsApp versions among them) do not show WebP link previews.
SIZES = {
    "logo": (160, "WEBP"),
    "avatar": (400, "WEBP"),
    "card": (640, "WEBP"),
    "featured": (1200, "WEBP"),
    "gallery": (1600, "WEBP"),
    "share": (1200, "JPEG"),
}
EXTENSIONS = {"WEBP": ".webp", "JPEG": ".jpg"}


@dataclass(frozen=True)
class Thumbnail:
    url: str
    width: int | None
    height: int | None

    @property
    def size_attrs(self):
        """width="..." height="..." for <img>, so the page does not jump while images load."""
        if not self.width:
            return ""
        return format_html('width="{}" height="{}"', self.width, self.height)


def thumbnail(image, size):
    """Thumbnail of an ImageField file for one of the SIZES, or None when there is no image.

    If the original cannot be read, the original URL is returned without
    dimensions, so the page still shows the image.
    """
    if not image:
        return None
    max_width, image_format = SIZES[size]
    name = thumb_name(image.name, size, image_format)
    cache_key = f"thumb:{name}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    storage = image.storage
    try:
        if storage.exists(name):
            with storage.open(name) as stored:
                width, height = Image.open(stored).size
        else:
            content, width, height = render(image, max_width, image_format)
            storage.save(name, ContentFile(content))
    except (OSError, ValueError) as error:
        logger.warning("Could not make %s thumbnail of %s: %s", size, image.name, error)
        return Thumbnail(image.url, None, None)

    thumb = Thumbnail(storage.url(name), width, height)
    cache.set(cache_key, thumb, timeout=None)
    return thumb


def thumb_name(original_name, size, image_format):
    path = PurePosixPath(original_name)
    return str(PurePosixPath("thumbs", size, path.parent, path.stem + EXTENSIONS[image_format]))


def render(image, max_width, image_format):
    """Resize (never enlarge) and encode. Returns (bytes, width, height)."""
    with image.open("rb") as original, Image.open(original) as picture:
        picture = ImageOps.exif_transpose(picture)  # phone photos keep their rotation
        if picture.width > max_width:
            height = round(picture.height * max_width / picture.width)
            picture = picture.resize((max_width, height), Image.Resampling.LANCZOS)

        if image_format == "JPEG":
            picture = flatten(picture)
        elif picture.mode not in ("RGB", "RGBA"):
            picture = picture.convert("RGBA" if has_alpha(picture) else "RGB")

        buffer = BytesIO()
        if image_format == "WEBP":
            picture.save(buffer, "WEBP", quality=82, method=6)
        else:
            picture.save(buffer, "JPEG", quality=85, optimize=True, progressive=True)
        return buffer.getvalue(), picture.width, picture.height


def has_alpha(picture):
    return picture.mode in ("RGBA", "LA", "PA") or "transparency" in picture.info


def flatten(picture):
    """JPEG has no transparency: put transparent images on a white background."""
    if not has_alpha(picture):
        return picture.convert("RGB")
    picture = picture.convert("RGBA")
    background = Image.new("RGB", picture.size, "white")
    background.paste(picture, mask=picture.getchannel("A"))
    return background
