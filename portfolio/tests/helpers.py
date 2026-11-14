"""Shared test helpers: fake uploads and a throwaway media folder."""

import io
import os
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image


def make_png(name="test.png", size=(20, 20)):
    """A tiny real PNG upload."""
    buffer = io.BytesIO()
    Image.new("RGB", size, "gray").save(buffer, "PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def make_big_png(megabytes=10):
    """A real PNG bigger than the 5 MB limit (random pixels do not compress)."""
    side = int((megabytes * 1024 * 1024 / 3) ** 0.5) + 1
    buffer = io.BytesIO()
    Image.frombytes("RGB", (side, side), os.urandom(side * side * 3)).save(buffer, "PNG")
    return SimpleUploadedFile("big.png", buffer.getvalue(), content_type="image/png")


class TempMediaMixin:
    """Save uploads to a temp folder that is deleted after the test class runs."""

    @classmethod
    def setUpClass(cls):
        cls._media_root = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_root)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)


class AdminLoginMixin:
    """Log in as a superuser before each test."""

    def setUp(self):
        super().setUp()
        user = get_user_model().objects.create_superuser("boss", password="test-pass")
        self.client.force_login(user)
