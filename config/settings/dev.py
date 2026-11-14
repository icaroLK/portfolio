"""
Settings for running the site on your own computer.

manage.py uses this file by default.
"""

from .base import *  # noqa: F401,F403

DEBUG = True

# Accept local addresses even if .env leaves ALLOWED_HOSTS empty.
ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1"]  # noqa: F405

# Emails are printed in the terminal instead of being sent.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
