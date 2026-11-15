"""
Settings for the live server (icarokucha.com).

The server uses this file through wsgi.py / asgi.py (and the Docker image sets it
for manage.py too).

How a visit reaches Django:
    visitor -> Cloudflare (HTTPS) -> tunnel -> cloudflared -> Caddy (localhost:8000)
    -> Gunicorn (localhost:8001) -> Django
"""

from .base import *  # noqa: F401,F403

DEBUG = False

# Compressed, cache-friendly static files served by WhiteNoise.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# HTTPS only. Cloudflare holds the certificate and talks HTTPS with the visitor.
# The tunnel and Caddy are plain HTTP inside the server, so Django learns the visit
# was secure from the X-Forwarded-Proto header Cloudflare adds (Caddy passes it on).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # one year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

# Cloudflare puts the visitor's real IP in CF-Connecting-IP (contact rate limit and
# admin lockout). Safe because only the tunnel can reach the server; see config/client_ip.py.
CLIENT_IP_HEADER = "HTTP_CF_CONNECTING_IP"

# Errors go to the terminal (docker compose logs) and to a small rotating file
# in logs/, which survives container restarts.
LOG_DIR = Path(env("LOG_DIR", default=str(BASE_DIR / "logs")))  # noqa: F405
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "plain"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "django.log",
            "maxBytes": 1024 * 1024,  # 1 MB per file, 5 files: the small disk never fills up
            "backupCount": 5,
            "formatter": "plain",
            "level": "WARNING",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
}

# Contact notifications go out through Resend's HTTP API, not SMTP: the server only has
# IPv6, and Resend's SMTP server only has IPv4, while api.resend.com has both.
# The address that receives them is set in the admin, under Site settings.
EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"
ANYMAIL = {
    "RESEND_API_KEY": env("RESEND_API_KEY", default=""),  # noqa: F405
    "REQUESTS_TIMEOUT": 10,  # seconds; a slow provider must not hang the form
}
