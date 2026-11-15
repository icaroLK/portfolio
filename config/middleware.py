"""Small project-wide middleware."""

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalHostMiddleware:
    """Sends www.icarokucha.com visitors to icarokucha.com (same page, HTTPS).

    One address keeps Google from seeing two copies of every page.
    Does nothing when CANONICAL_HOST is empty (your computer).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = settings.CANONICAL_HOST
        if host and request.get_host() == f"www.{host}":
            return HttpResponsePermanentRedirect(f"https://{host}{request.get_full_path()}")
        return self.get_response(request)


class NoIndexAdminMiddleware:
    """Tells search engines never to index admin pages.

    This is done with a header instead of a robots.txt line, because robots.txt
    is public and would reveal the secret admin path.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.prefix = f"/{settings.ADMIN_PATH}/"

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(self.prefix):
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response
