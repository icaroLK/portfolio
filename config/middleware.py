"""Small project-wide middleware."""

from django.conf import settings


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
