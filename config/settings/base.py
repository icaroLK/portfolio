"""
Settings shared by every environment (your computer and the server).

dev.py and prod.py import everything from here and only change what differs.
Secrets and anything that changes per machine come from the .env file.
"""

from pathlib import Path

import environ

# Project root: the folder that holds manage.py.
# This file is config/settings/base.py, so we go up three levels.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


# --- Security and secrets (always from .env) ---

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# The admin lives on a private path instead of the well-known /admin/.
# Stored without slashes, for example "painel-8x2k".
ADMIN_PATH = env("ADMIN_PATH").strip("/")


# --- Apps ---

INSTALLED_APPS = [
    # Our admin site (shows the site name in the header), replaces django.contrib.admin.
    "config.admin.PortfolioAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # WhiteNoise also serves CSS/JS in dev, with "always re-check" headers, so the
    # browser never keeps an old site.css after a rebuild. Must sit above staticfiles.
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    # Drag-and-drop ordering in the admin
    "adminsortable2",
    # Our apps
    "portfolio",
    "contact",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise must come right after SecurityMiddleware to serve static files.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# --- Templates ---

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Site-wide templates (base.html, partials) live in /templates.
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Site settings (name, links, resume) on every page
                "portfolio.context_processors.site",
            ],
        },
    },
]


# --- Database ---
# SQLite file in the project root unless DATABASE_URL says otherwise.

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Passwords ---

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Language and time ---

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


# --- Static files (CSS, JS, fonts) and media (uploads) ---

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]   # where we write our CSS
STATIC_ROOT = BASE_DIR / "staticfiles"     # where collectstatic gathers everything

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"            # uploaded images and the resume PDF


# --- Contact form ---

# Sender address of the notification emails (the recipient is set in Site settings).
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="webmaster@localhost")

# Only true behind a proxy that sets X-Forwarded-For (Caddy in production).
# Otherwise visitors could fake their IP and skip the rate limit.
TRUST_X_FORWARDED_FOR = False
