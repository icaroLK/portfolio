from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from portfolio.models import SiteSettings
from portfolio.views import render_about

from .forms import ContactForm
from .models import ContactMessage
from .notifications import notify_new_message

RATE_LIMIT_ERROR = (
    "You have sent a few messages in the last hour. "
    "Please try again later, or email me directly."
)


def sent_url():
    return reverse("portfolio:about") + "?sent=1#contact"


def client_ip(request):
    """The visitor's IP address.

    In production Caddy sits in front of Django, so REMOTE_ADDR is Caddy itself
    and the real address is the last entry Caddy added to X-Forwarded-For.
    The last entry is used because anything before it can be faked by the visitor.
    """
    if settings.TRUST_X_FORWARDED_FOR:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR")


@require_POST
def contact_submit(request):
    """Validate, save, email, then redirect (so a refresh never sends twice)."""
    if not SiteSettings.load().show_contact_form:
        return redirect(reverse("portfolio:about") + "#contact")

    form = ContactForm(request.POST)

    # Bots get the normal success page, but nothing is saved or emailed.
    if form.is_spam():
        return redirect(sent_url())

    ip = client_ip(request)
    if form.is_valid() and ContactMessage.objects.limit_reached(ip):
        form.add_error(None, RATE_LIMIT_ERROR)

    if not form.is_valid():
        return render_about(request, form, status=400)

    message = form.save(commit=False)
    message.ip_address = ip
    message.user_agent = request.META.get("HTTP_USER_AGENT", "")[:300]
    message.save()

    message.email_sent = notify_new_message(message)
    message.save(update_fields=["email_sent"])

    return redirect(sent_url())
