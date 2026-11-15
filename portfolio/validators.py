"""
Field rules: uploads (images, resume) and time zone names.

Images: jpg, png or webp, max 5 MB. Resume: pdf, max 5 MB.
Uploaded files also get a random name, so nobody can guess or overwrite them.
"""

from pathlib import Path
from uuid import uuid4
from zoneinfo import available_timezones

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible

MAX_UPLOAD_MB = 5
IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


def validate_file_size(file):
    """Reject files bigger than MAX_UPLOAD_MB."""
    limit = MAX_UPLOAD_MB * 1024 * 1024
    if file.size > limit:
        size_mb = file.size / (1024 * 1024)
        raise ValidationError(
            f"This file is {size_mb:.1f} MB. The maximum is {MAX_UPLOAD_MB} MB."
        )


validate_image_extension = FileExtensionValidator(
    allowed_extensions=IMAGE_EXTENSIONS,
    message="Only JPG, PNG or WEBP images are allowed.",
)

validate_pdf_extension = FileExtensionValidator(
    allowed_extensions=["pdf"],
    message="Only PDF files are allowed.",
)

IMAGE_VALIDATORS = [validate_image_extension, validate_file_size]
PDF_VALIDATORS = [validate_pdf_extension, validate_file_size]


# @deconstructible lets Django write this class into migration files.
@deconstructible
class RandomFilename:
    """Save uploads as <folder>/<random hex>.<ext>, e.g. projects/3f9a....webp."""

    def __init__(self, folder):
        self.folder = folder

    def __call__(self, instance, filename):
        extension = Path(filename).suffix.lower()
        return f"{self.folder}/{uuid4().hex}{extension}"

    def __eq__(self, other):
        return isinstance(other, RandomFilename) and self.folder == other.folder


def validate_time_zone(value):
    """Accept only real time zone names like "America/Sao_Paulo"."""
    if value and value not in available_timezones():
        raise ValidationError(f'"{value}" is not a time zone name, e.g. "America/Sao_Paulo".')
