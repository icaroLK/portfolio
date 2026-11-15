"""
Settings shared by every environment (your computer and the server).

dev.py and prod.py import everything from here and only change what differs.
Secrets and anything that changes per machine come from the .env file.
"""

from datetime import timedelta
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
    # Modern admin theme. Must come before the admin app.
    "unfold.apps.BasicAppConfig",  # basic: keeps our admin site below instead of swapping in its own
    # Our admin site (shows the site name in the header), replaces django.contrib.admin.
    "config.admin.PortfolioAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sitemaps",
    # WhiteNoise also serves CSS/JS in dev, with "always re-check" headers, so the
    # browser never keeps an old site.css after a rebuild. Must sit above staticfiles.
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    # Locks the admin login after too many wrong passwords
    "axes",
    # Contact emails through an HTTP API (the server cannot reach SMTP, see prod.py)
    "anymail",
    # Our apps
    "portfolio",
    "contact",
]

MIDDLEWARE = [
    # First, so http://www. goes straight to https:// without a second redirect.
    "config.middleware.CanonicalHostMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise must come right after SecurityMiddleware to serve static files.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.NoIndexAdminMiddleware",
    # Last, as django-axes asks: it turns a lockout into the "try again later" page.
    "axes.middleware.AxesMiddleware",
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


# --- Login and passwords ---

AUTHENTICATION_BACKENDS = [
    # Checked first: refuses any login from a locked-out IP.
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Admin lockout: 5 wrong passwords from the same IP lock the login for 1 hour.
# Locking by IP (not by username) means an attacker cannot lock you out from elsewhere.
# Unlock early on the server with: manage.py axes_reset
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_LOCKOUT_PARAMETERS = ["ip_address"]
AXES_RESET_ON_SUCCESS = True
AXES_CLIENT_IP_CALLABLE = "config.client_ip.client_ip"
AXES_LOCKOUT_TEMPLATE = "axes_lockout.html"
AXES_ENABLE_ADMIN = False  # keeps the admin sidebar clean; the command above is enough

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


# --- Admin look (django-unfold) ---

# Warm grays that match the site's colors (Tailwind "stone" scale).
_STONE = {
    "50": "oklch(98.5% .001 106.423)",
    "100": "oklch(97% .001 106.424)",
    "200": "oklch(92.3% .003 48.717)",
    "300": "oklch(86.9% .005 56.366)",
    "400": "oklch(70.9% .01 56.259)",
    "500": "oklch(55.3% .013 58.071)",
    "600": "oklch(44.4% .011 73.639)",
    "700": "oklch(37.4% .01 67.558)",
    "800": "oklch(26.8% .007 34.298)",
    "900": "oklch(21.6% .006 56.043)",
    "950": "oklch(14.7% .004 49.25)",
}


def _admin_link(name):
    # Imported here: URLs are not ready yet when settings load.
    from django.urls import reverse_lazy

    return reverse_lazy(f"admin:{name}")


UNFOLD = {
    "SITE_TITLE": "config.admin.admin_title",
    "SITE_HEADER": "config.admin.site_name",
    "SITE_SYMBOL": "edit_note",
    "SITE_URL": "/",
    "SHOW_VIEW_ON_SITE": True,
    "BORDER_RADIUS": "10px",
    "COLORS": {"base": _STONE, "primary": _STONE},
    # Three groups of similar size. The name at the top of the sidebar is the Home link
    # (templates/unfold/helpers/site_icon.html), and the home page lists these same groups.
    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Site",
                "items": [
                    {"title": "Site settings", "icon": "tune",
                     "link": _admin_link("portfolio_sitesettings_changelist")},
                    {"title": "Inbox", "icon": "inbox",
                     "link": _admin_link("contact_contactmessage_changelist"),
                     "badge": "config.admin.unread_messages_badge"},
                    {"title": "Users", "icon": "person",
                     "link": _admin_link("auth_user_changelist")},
                ],
            },
            {
                "title": "Projects",
                "items": [
                    {"title": "Projects", "icon": "work",
                     "link": _admin_link("portfolio_project_changelist")},
                    {"title": "Type tags", "icon": "label",
                     "link": _admin_link("portfolio_typetag_changelist")},
                    {"title": "Techs", "icon": "code",
                     "link": _admin_link("portfolio_tech_changelist")},
                ],
            },
            {
                "title": "About page",
                "items": [
                    {"title": "Experience", "icon": "badge",
                     "link": _admin_link("portfolio_experience_changelist")},
                    {"title": "Education", "icon": "school",
                     "link": _admin_link("portfolio_education_changelist")},
                    {"title": "Skill groups", "icon": "construction",
                     "link": _admin_link("portfolio_skillgroup_changelist")},
                    {"title": "Services", "icon": "storefront",
                     "link": _admin_link("portfolio_service_changelist")},
                ],
            },
        ],
    },
}


# --- Contact form ---

# Sender address of the notification emails (the recipient is set in Site settings).
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="webmaster@localhost")


# --- Visitor IP and main address ---

# Request header that holds the visitor's real IP (see config/client_ip.py).
# Empty on your computer: REMOTE_ADDR is used, so nobody can fake their IP.
CLIENT_IP_HEADER = None

# The site's one true address, without www (www. redirects to it). Empty = no redirect.
CANONICAL_HOST = env("CANONICAL_HOST", default="")
