"""Email sent to Ícaro when a new contact form message arrives."""

import logging

from django.conf import settings
from django.core.mail import EmailMessage

from portfolio.models import SiteSettings

logger = logging.getLogger(__name__)


def notify_new_message(message):
    """Email the message to the notification address in Site settings.

    Returns True when the email went out. Never raises: if the provider is
    down, the message is already saved in the inbox and the error is logged.
    """
    recipient = SiteSettings.load().notification_email
    if not recipient:
        logger.warning("Contact message %s saved, but no notification email is set.", message.pk)
        return False

    email = EmailMessage(
        subject=f"New message from {message.name} ({message.get_topic_display()})",
        body=(
            f"Name: {message.name}\n"
            f"Email: {message.email}\n"
            f"Topic: {message.get_topic_display()}\n\n"
            f"{message.message}\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
        reply_to=[message.email],  # hitting Reply answers the visitor directly
    )
    try:
        email.send()
    except Exception:
        logger.exception("Could not send the notification email for message %s.", message.pk)
        return False
    return True
