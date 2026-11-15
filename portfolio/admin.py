from zoneinfo import available_timezones

from django.contrib import admin
from django.db import models
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.widgets import UnfoldAdminCheckboxSelectMultipleWidget, UnfoldAdminSelect2Widget

from .models import (
    Education,
    Experience,
    Language,
    Project,
    ProjectFeature,
    ProjectImage,
    ProjectTech,
    Service,
    SiteSettings,
    Skill,
    SkillGroup,
    Tech,
    TypeTag,
)
from .widgets import MarkdownTextarea, MonthYearWidget

# In "fields" and "fieldsets", a tuple puts its fields side by side on one row.
# "collapse" folds a section that is rarely edited.


def image_preview(image_field, height=120):
    """Small <img> tag for showing an uploaded image inside the admin."""
    if not image_field:
        return "No image yet"
    return format_html(
        '<img src="{}" alt="" style="height:{}px;width:auto;border-radius:8px">',
        image_field.url,
        height,
    )


class MarkdownFieldsMixin:
    """Gives the text boxes listed in `markdown_fields` the formatting toolbar."""

    markdown_fields = []

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.markdown_fields:
            kwargs["widget"] = MarkdownTextarea
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class MonthYearDatesMixin:
    """Every date on the page is picked as month + year (no day, no calendar)."""

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, models.DateField):
            kwargs["widget"] = MonthYearWidget
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class SortableAdmin(ModelAdmin):
    """List with drag-and-drop rows (grab the handle, then click Save)."""

    ordering_field = "order"
    hide_ordering_field = True


class SortableInline(TabularInline):
    """Inline rows that can be dragged into order."""

    ordering_field = "order"
    hide_ordering_field = True
    extra = 1


class LanguageInline(SortableInline):
    model = Language
    fields = ["name", "level", "order"]
    verbose_name_plural = "Languages (About page)"


@admin.register(SiteSettings)
class SiteSettingsAdmin(MarkdownFieldsMixin, ModelAdmin):
    """One edit page, no Add or Delete. The list page jumps straight to it."""

    markdown_fields = ["about_bio"]
    inlines = [LanguageInline]
    readonly_fields = ["profile_photo_preview", "og_image_preview"]
    fieldsets = [
        ("Hero", {"fields": [
            "site_name", "headline", "subheadline",
            ("status_badge_text", "show_status_badge"),
        ]}),
        ("About", {"fields": [
            "about_heading", "about_bio", ("profile_photo", "profile_photo_preview"),
            "services_intro", ("contact_heading", "contact_text"),
        ]}),
        ("Links & resume", {"fields": [
            "resume_pdf", ("email", "location_line"), ("github_url", "linkedin_url"),
        ]}),
        ("Quick facts (About page)", {
            "description": (
                "Shown next to your photo with small icons. Email, GitHub and LinkedIn "
                "come from Links & resume. Languages are at the bottom of this page."
            ),
            "fields": [("about_location", "time_zone")],
        }),
        ("Contact form", {"fields": ["notification_email"]}),
        ("Section toggles", {
            "description": "Show or hide sections of the About page.",
            "fields": [
                ("show_experience", "show_education", "show_skills"),
                ("show_services", "show_contact_form"),
            ],
        }),
        ("SEO", {
            "classes": ["collapse"],
            "description": "Defaults for Google and link previews. Project pages use their own.",
            "fields": ["meta_description", ("og_image", "og_image_preview")],
        }),
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # A searchable dropdown of real zone names (type "Sao"), so a typo can never break the clock.
        if db_field.name == "time_zone":
            zones = sorted(available_timezones())
            kwargs["widget"] = UnfoldAdminSelect2Widget(
                choices=[("", "No clock")] + [(zone, zone) for zone in zones]
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    @admin.display(description="Current photo")
    def profile_photo_preview(self, obj):
        return image_preview(obj.profile_photo)

    @admin.display(description="Current share image")
    def og_image_preview(self, obj):
        return image_preview(obj.og_image)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        settings = SiteSettings.load()
        return redirect(reverse("admin:portfolio_sitesettings_change", args=[settings.pk]))


# --- Tags and techs ---


@admin.register(TypeTag)
class TypeTagAdmin(SortableAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]
    fields = [("name", "slug")]


@admin.register(Tech)
class TechAdmin(ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]
    fields = [("name", "slug")]


# --- Projects ---


class ProjectFeatureInline(SortableInline):
    model = ProjectFeature
    verbose_name_plural = "Key features"


class ProjectTechInline(SortableInline):
    model = ProjectTech
    autocomplete_fields = ["tech"]  # type to search; "+" adds a new tech
    verbose_name_plural = "Tech stack"


class ProjectImageInline(SortableInline):
    model = ProjectImage
    fields = ["image", "preview", "caption", "order"]
    readonly_fields = ["preview"]
    verbose_name_plural = "Gallery"

    @admin.display(description="Preview")
    def preview(self, obj):
        return image_preview(obj.image, height=60)


@admin.register(Project)
class ProjectAdmin(MarkdownFieldsMixin, SortableAdmin):
    list_display = ["thumbnail", "title", "tag_list", "is_featured", "is_published"]
    list_display_links = ["title"]
    list_editable = ["is_featured", "is_published"]
    markdown_fields = ["what_it_does", "how_it_works"]
    list_filter = ["type_tags", "is_featured", "is_published"]
    search_fields = ["title"]

    prepopulated_fields = {"slug": ["title"]}
    readonly_fields = ["cover_preview", "architecture_preview"]
    inlines = [ProjectFeatureInline, ProjectTechInline, ProjectImageInline]
    fieldsets = [
        ("Basics", {"fields": [
            ("title", "slug"),
            "pitch",
            "type_tags",
            ("role", "period"),
            ("is_featured", "is_published"),
        ]}),
        ("Media", {"fields": [("cover_image", "cover_preview"), "video_url"]}),
        ("Content", {"fields": [
            "what_it_does", "how_it_works", ("architecture_image", "architecture_preview"),
        ]}),
        ("Links", {"classes": ["collapse"], "fields": [("live_url", "repo_url")]}),
        ("SEO", {"classes": ["collapse"], "fields": ["seo_description"]}),
    ]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # A few tags: plain checkboxes are quicker than a two-box picker.
        if db_field.name == "type_tags":
            kwargs["widget"] = UnfoldAdminCheckboxSelectMultipleWidget
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self, request):
        # Load all tags in one extra query instead of one query per row.
        return super().get_queryset(request).prefetch_related("type_tags")

    @admin.display(description="Cover")
    def thumbnail(self, obj):
        return image_preview(obj.cover_image, height=40)

    @admin.display(description="Type tags")
    def tag_list(self, obj):
        return " · ".join(tag.name for tag in obj.type_tags.all())

    @admin.display(description="Current cover")
    def cover_preview(self, obj):
        return image_preview(obj.cover_image)

    @admin.display(description="Current diagram")
    def architecture_preview(self, obj):
        return image_preview(obj.architecture_image)


# --- About page ---


@admin.register(Experience)
class ExperienceAdmin(MonthYearDatesMixin, MarkdownFieldsMixin, SortableAdmin):
    markdown_fields = ["details"]
    radio_fields = {"work_mode": admin.HORIZONTAL}
    list_display = [
        "logo_thumbnail", "role", "company", "work_mode", "start_date", "end_date", "is_published",
    ]
    list_display_links = ["role"]
    list_editable = ["is_published"]
    list_filter = ["work_mode", "is_published"]
    search_fields = ["role", "company"]
    autocomplete_fields = ["techs"]
    readonly_fields = ["logo_preview"]
    fieldsets = [
        ("Job", {"fields": [
            ("role", "company"),
            ("location", "work_mode"),
            ("start_date", "end_date"),
            ("logo", "logo_preview"),
            "is_published",
        ]}),
        ("Text", {"fields": ["summary", "details"]}),
        ("Tech chips", {"fields": ["techs"]}),
    ]

    @admin.display(description="Logo")
    def logo_thumbnail(self, obj):
        return image_preview(obj.logo, height=32)

    @admin.display(description="Current logo")
    def logo_preview(self, obj):
        return image_preview(obj.logo, height=64)


@admin.register(Education)
class EducationAdmin(MonthYearDatesMixin, SortableAdmin):
    list_display = ["logo_thumbnail", "degree", "school", "start_date", "end_date", "is_published"]
    list_display_links = ["degree"]
    list_editable = ["is_published"]
    list_filter = ["is_published"]
    search_fields = ["degree", "school"]
    readonly_fields = ["logo_preview"]
    fields = [
        ("degree", "school"),
        ("city", "is_published"),
        ("start_date", "end_date"),
        "period_label",
        ("logo", "logo_preview"),
    ]

    @admin.display(description="Logo")
    def logo_thumbnail(self, obj):
        return image_preview(obj.logo, height=32)

    @admin.display(description="Current logo")
    def logo_preview(self, obj):
        return image_preview(obj.logo, height=64)


class SkillInline(SortableInline):
    model = Skill


@admin.register(SkillGroup)
class SkillGroupAdmin(SortableAdmin):
    list_display = ["name", "skill_list"]
    inlines = [SkillInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("skills")

    @admin.display(description="Skills")
    def skill_list(self, obj):
        return ", ".join(skill.name for skill in obj.skills.all())


@admin.register(Service)
class ServiceAdmin(MarkdownFieldsMixin, SortableAdmin):
    markdown_fields = ["description"]
    list_display = ["title", "description", "is_published"]
    list_editable = ["is_published"]
    fields = ["title", "description", "is_published"]


# --- Users: same admin as Django's, in the Unfold style ---

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
