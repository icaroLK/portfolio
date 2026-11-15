"""The visitor's real IP address, used by the contact rate limit and the admin lockout."""

from django.conf import settings


def client_ip(request):
    """Return the visitor's IP address.

    On the live server, visitors reach Django through Cloudflare, cloudflared and Caddy,
    so REMOTE_ADDR is always 127.0.0.1. Cloudflare puts the real address in the
    CF-Connecting-IP header, and CLIENT_IP_HEADER (set in prod.py) names that header.

    Trusting the header is safe there because Caddy and Gunicorn only listen on
    localhost: the tunnel is the only way in, so nobody can send a fake header
    straight to the server. On your computer the setting is empty and REMOTE_ADDR is used.
    """
    header = settings.CLIENT_IP_HEADER
    if header:
        value = request.META.get(header, "").strip()
        if value:
            return value
    return request.META.get("REMOTE_ADDR")
