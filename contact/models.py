from datetime import timedelta

from django.db import models
from django.utils import timezone

from portfolio.models import TimeStampedModel

# Contact form rate limit: at most this many messages per IP address per hour.
MAX_MESSAGES_PER_HOUR = 3


class ContactMessageQuerySet(models.QuerySet):
    def sent_in_last_hour_from(self, ip_address):
        return self.filter(
            ip_address=ip_address, created_at__gte=timezone.now() - timedelta(hours=1)
        )

    def limit_reached(self, ip_address):
        return self.sent_in_last_hour_from(ip_address).count() >= MAX_MESSAGES_PER_HOUR


class ContactMessage(TimeStampedModel):
    """A message sent through the contact form on the About page."""

    class Topic(models.TextChoices):
        JOB = "job", "Job opportunity"
        BUSINESS = "business", "Website or system for my business"
        OTHER = "other", "Other"

    name = models.CharField(max_length=120)
    email = models.EmailField()
    topic = models.CharField(max_length=20, choices=Topic.choices, default=Topic.OTHER)
    message = models.TextField()

    # Filled in automatically when the form is sent (rate limit and spam review).
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)

    is_read = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)
    email_sent = models.BooleanField(
        default=False, help_text="Whether the notification email was delivered."
    )

    objects = ContactMessageQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]  # newest first
        verbose_name = "message"
        verbose_name_plural = "Inbox"

    def __str__(self):
        return f"{self.name} ({self.get_topic_display()})"
