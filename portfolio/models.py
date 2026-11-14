"""
Database tables for all the site content edited in the admin.

Every list model has an `order` field (drag-and-drop in the admin) and,
where it makes sense, `is_published` (hidden from the site when off).
"""

from django.db import models
from django.utils.text import slugify

from .validators import IMAGE_VALIDATORS, PDF_VALIDATORS, RandomFilename


# --- Shared building blocks ---


class TimeStampedModel(models.Model):
    """Adds created_at and updated_at to every model that inherits it."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # no table of its own, only adds fields to children


class PublishedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


# --- Site settings (one row only) ---


class SiteSettings(TimeStampedModel):
    """Global texts, links and toggles. There is always exactly one row (pk=1)."""

    # Hero
    site_name = models.CharField(max_length=80)
    headline = models.CharField(max_length=200)
    subheadline = models.CharField(max_length=300, blank=True)
    status_badge_text = models.CharField(max_length=80, blank=True)
    show_status_badge = models.BooleanField(default=True)

    # About
    about_bio = models.TextField(blank=True)
    profile_photo = models.ImageField(
        upload_to=RandomFilename("site"), blank=True, validators=IMAGE_VALIDATORS
    )

    # Links and resume
    resume_pdf = models.FileField(
        upload_to=RandomFilename("resume"), blank=True, validators=PDF_VALIDATORS
    )
    email = models.EmailField(blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    location_line = models.CharField(max_length=120, blank=True)

    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    og_image = models.ImageField(
        "Open Graph image",
        upload_to=RandomFilename("site"),
        blank=True,
        validators=IMAGE_VALIDATORS,
    )

    # About page section toggles
    show_experience = models.BooleanField(default=True)
    show_education = models.BooleanField(default=True)
    show_skills = models.BooleanField(default=True)
    show_services = models.BooleanField(default=True)
    show_contact_form = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # always the same row, so a second one can never exist
        if self.created_at is None:
            # A fresh object saved over the existing row keeps the row's creation date.
            self.created_at = (
                SiteSettings.objects.filter(pk=1).values_list("created_at", flat=True).first()
            )
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Return the single settings row, creating an empty one if needed."""
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings


# --- Tags and technologies ---


class TypeTag(TimeStampedModel):
    """Project category like "Computer Vision". Drives the Home filters."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Tech(TimeStampedModel):
    """A technology like "Django". Used in project stacks and experience chips."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Techs"

    def __str__(self):
        return self.name


# --- Projects ---


class Project(TimeStampedModel):
    # Basics
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    pitch = models.CharField(max_length=200, help_text="Plain-language line for cards.")
    type_tags = models.ManyToManyField(TypeTag, related_name="projects", blank=True)
    role = models.CharField(max_length=80, blank=True, help_text='e.g. "Solo project"')
    period = models.CharField(max_length=40, blank=True, help_text='e.g. "Nov 2026"')

    # Media
    cover_image = models.ImageField(
        upload_to=RandomFilename("projects"), validators=IMAGE_VALIDATORS
    )
    video_url = models.URLField(blank=True, help_text="YouTube or Loom link.")

    # Links
    live_url = models.URLField(blank=True)
    repo_url = models.URLField(blank=True)

    # Content
    what_it_does = models.TextField(help_text="Plain language, for non-technical readers.")
    how_it_works = models.TextField(blank=True, help_text="Technical. Simple Markdown.")
    architecture_image = models.ImageField(
        upload_to=RandomFilename("projects"), blank=True, validators=IMAGE_VALIDATORS
    )

    # Visibility and order
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    # SEO
    seo_description = models.CharField(
        max_length=160, blank=True, help_text="Leave empty to use the pitch."
    )

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # Sprint 4 adds the project page route; switch this to reverse() then.
        return f"/projects/{self.slug}/"


class ProjectFeature(TimeStampedModel):
    """One numbered row in "Key features"."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="features")
    text = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text


class ProjectTech(TimeStampedModel):
    """One chip in a project's "Tech stack": a tech plus what it was used for."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="stack")
    # PROTECT: a tech used by a project cannot be deleted by accident.
    tech = models.ForeignKey(Tech, on_delete=models.PROTECT, related_name="project_uses")
    purpose = models.CharField(max_length=40, help_text='e.g. "car detection"')
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "stack item"

    def __str__(self):
        return f"{self.tech} ({self.purpose})"


class ProjectImage(TimeStampedModel):
    """One image in a project's gallery."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(
        upload_to=RandomFilename("projects/gallery"), validators=IMAGE_VALIDATORS
    )
    caption = models.CharField(max_length=120, blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "gallery image"

    def __str__(self):
        return self.caption or f"Image {self.pk}"


# --- About page ---


class Experience(TimeStampedModel):
    role = models.CharField(max_length=120)
    company = models.CharField(max_length=120)
    location = models.CharField(max_length=120, blank=True, help_text='e.g. "Remote (US)"')
    logo = models.ImageField(
        upload_to=RandomFilename("logos"), blank=True, validators=IMAGE_VALIDATORS
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Empty means Present.")
    summary = models.CharField(max_length=300, help_text="Always visible.")
    details = models.TextField(
        blank=True, help_text='Simple Markdown. "Show details" appears only when filled.'
    )
    techs = models.ManyToManyField(Tech, related_name="experiences", blank=True)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.role} at {self.company}"


class Education(TimeStampedModel):
    degree = models.CharField(max_length=120)
    school = models.CharField(max_length=120)
    city = models.CharField(max_length=120, blank=True)
    logo = models.ImageField(
        upload_to=RandomFilename("logos"), blank=True, validators=IMAGE_VALIDATORS
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    period_label = models.CharField(
        max_length=80, blank=True, help_text='Optional, e.g. "Erasmus semester, 2026".'
    )
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Education"

    def __str__(self):
        return f"{self.degree}, {self.school}"


class SkillGroup(TimeStampedModel):
    name = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Skill(TimeStampedModel):
    group = models.ForeignKey(SkillGroup, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=60)
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Service(TimeStampedModel):
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=200)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title
