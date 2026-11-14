from adminsortable2.admin import SortableAdminMixin, SortableTabularInline
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Education,
    Experience,
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


def image_preview(image_field, height=120):
    """Small <img> tag for showing an uploaded image inside the admin."""
    if not image_field:
        return "No image yet"
    return format_html(
        '<img src="{}" alt="" style="height:{}px;width:auto;border-radius:8px">',
        image_field.url,
        height,
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """One edit page, no Add or Delete. The list page jumps straight to it."""

    readonly_fields = ["profile_photo_preview", "og_image_preview"]
    fieldsets = [
        ("Hero", {"fields": [
            "site_name", "headline", "subheadline",
            "status_badge_text", "show_status_badge",
        ]}),
        ("About", {"fields": [
            "about_heading", "about_bio", "profile_photo", "profile_photo_preview",
            "services_intro", "contact_heading", "contact_text",
        ]}),
        ("Contact form", {"fields": ["notification_email"]}),
        ("Links & resume", {"fields": [
            "resume_pdf", "email", "github_url", "linkedin_url", "location_line",
        ]}),
        ("SEO", {"fields": ["meta_description", "og_image", "og_image_preview"]}),
        ("Section toggles", {
            "description": "Show or hide sections of the About page.",
            "fields": [
                "show_experience", "show_education", "show_skills",
                "show_services", "show_contact_form",
            ],
        }),
    ]

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
class TypeTagAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


@admin.register(Tech)
class TechAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


# --- Projects ---


class ProjectFeatureInline(SortableTabularInline):
    model = ProjectFeature
    extra = 1
    verbose_name_plural = "Key features"


class ProjectTechInline(SortableTabularInline):
    model = ProjectTech
    extra = 1
    autocomplete_fields = ["tech"]  # type to search; "+" adds a new tech
    verbose_name_plural = "Tech stack"


class ProjectImageInline(SortableTabularInline):
    model = ProjectImage
    extra = 1
    fields = ["image", "preview", "caption"]
    readonly_fields = ["preview"]
    verbose_name_plural = "Gallery"

    @admin.display(description="Preview")
    def preview(self, obj):
        return image_preview(obj.image, height=60)


@admin.register(Project)
class ProjectAdmin(SortableAdminMixin, admin.ModelAdmin):
    # The drag handle column is added first automatically by SortableAdminMixin.
    list_display = ["thumbnail", "title", "tag_list", "is_featured", "is_published"]
    list_display_links = ["title"]
    list_editable = ["is_featured", "is_published"]
    list_filter = ["type_tags", "is_featured", "is_published"]
    search_fields = ["title"]

    prepopulated_fields = {"slug": ["title"]}
    filter_horizontal = ["type_tags"]
    readonly_fields = ["cover_preview", "architecture_preview"]
    inlines = [ProjectFeatureInline, ProjectTechInline, ProjectImageInline]
    fieldsets = [
        ("Basics", {"fields": [
            "title", "slug", "pitch", "type_tags", "role", "period",
            "is_featured", "is_published",
        ]}),
        ("Media", {"fields": ["cover_image", "cover_preview", "video_url"]}),
        ("Content", {"fields": [
            "what_it_does", "how_it_works", "architecture_image", "architecture_preview",
        ]}),
        ("Links", {"fields": ["live_url", "repo_url"]}),
        ("SEO", {"fields": ["seo_description"]}),
    ]

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
class ExperienceAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["logo_thumbnail", "role", "company", "start_date", "end_date", "is_published"]
    list_display_links = ["role"]
    list_editable = ["is_published"]
    list_filter = ["is_published"]
    search_fields = ["role", "company"]
    autocomplete_fields = ["techs"]
    readonly_fields = ["logo_preview"]
    fields = [
        "role", "company", "location", "logo", "logo_preview",
        "start_date", "end_date", "summary", "details", "techs", "is_published",
    ]

    @admin.display(description="Logo")
    def logo_thumbnail(self, obj):
        return image_preview(obj.logo, height=32)

    @admin.display(description="Current logo")
    def logo_preview(self, obj):
        return image_preview(obj.logo, height=64)


@admin.register(Education)
class EducationAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["logo_thumbnail", "degree", "school", "start_date", "end_date", "is_published"]
    list_display_links = ["degree"]
    list_editable = ["is_published"]
    list_filter = ["is_published"]
    search_fields = ["degree", "school"]
    readonly_fields = ["logo_preview"]
    fields = [
        "degree", "school", "city", "logo", "logo_preview",
        "start_date", "end_date", "period_label", "is_published",
    ]

    @admin.display(description="Logo")
    def logo_thumbnail(self, obj):
        return image_preview(obj.logo, height=32)

    @admin.display(description="Current logo")
    def logo_preview(self, obj):
        return image_preview(obj.logo, height=64)


class SkillInline(SortableTabularInline):
    model = Skill
    extra = 1


@admin.register(SkillGroup)
class SkillGroupAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["name", "skill_list"]
    inlines = [SkillInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("skills")

    @admin.display(description="Skills")
    def skill_list(self, obj):
        return ", ".join(skill.name for skill in obj.skills.all())


@admin.register(Service)
class ServiceAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["title", "description", "is_published"]
    list_editable = ["is_published"]
