from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(ModelAdmin):
    """Inbox: messages can be read, marked and deleted, but never edited."""

    list_display = ["created_at", "name", "email", "topic", "is_read", "is_spam", "email_sent"]
    list_display_links = ["created_at", "name"]
    list_filter = ["is_read", "is_spam", "email_sent", "topic"]
    search_fields = ["name", "email", "message"]
    date_hierarchy = "created_at"
    actions = ["mark_as_read", "mark_as_spam"]

    def has_add_permission(self, request):
        return False  # messages only come from the contact form

    def has_change_permission(self, request, obj=None):
        return False  # opening a message shows it read-only

    def changelist_view(self, request, extra_context=None):
        unread = ContactMessage.objects.filter(is_read=False, is_spam=False).count()
        extra_context = {**(extra_context or {}), "title": f"Inbox ({unread} unread)"}
        return super().changelist_view(request, extra_context)

    @admin.action(description="Mark as read")
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} message(s) marked as read.")

    @admin.action(description="Mark as spam")
    def mark_as_spam(self, request, queryset):
        updated = queryset.update(is_spam=True, is_read=True)
        self.message_user(request, f"{updated} message(s) marked as spam.")
