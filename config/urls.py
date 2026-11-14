"""
Main URL list: maps each web address to the code that answers it.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Private admin path from .env (never the default /admin/).
    path(f"{settings.ADMIN_PATH}/", admin.site.urls),
    # Public pages (home, projects, about) live in the portfolio app.
    path("", include("portfolio.urls")),
]

# In dev, Django serves uploaded files (in production Caddy does it).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
