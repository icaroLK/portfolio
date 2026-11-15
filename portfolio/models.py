"""
Database tables for all the site content edited in the admin.

Every list model has an `order` field (drag-and-drop in the admin) and,
where it makes sense, `is_published` (hidden from the site when off).
"""

from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import dateformat
from django.utils.text import slugify

from .embeds import embed_url, validate_video_url
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


class ProjectQuerySet(PublishedQuerySet):
    """Project lists for the Home page. Each one is published only, in admin order."""

    def featured(self):
        return self.published().filter(is_featured=True)

    def archive(self):
        return self.published().filter(is_featured=False)

    def for_cards(self):
        # Load tags and stack (with each tech) in 3 extra queries in total,
        # instead of 2 more queries for every card on the page.
        return self.prefetch_related(
            "type_tags",
            models.Prefetch("stack", queryset=ProjectTech.objects.select_related("tech")),
        )

    def for_detail(self):
        """Everything the project page shows, in a fixed number of queries."""
        return self.for_cards().prefetch_related("features", "gallery")


class ExperienceQuerySet(PublishedQuerySet):
    def for_about(self):
        return self.published().prefetch_related("techs")


class SkillGroupQuerySet(models.QuerySet):
    def for_about(self):
        """Groups with at least one skill, each with its skills loaded in one extra query."""
        return self.filter(skills__isnull=False).distinct().prefetch_related("skills")


def date_range(start, end):
    """Label like "Mar 2025 – Present". An empty end date means Present."""
    end_label = dateformat.format(end, "M Y") if end else "Present"
    return f"{dateformat.format(start, 'M Y')} – {end_label}"


class TypeTagQuerySet(models.QuerySet):
    def in_archive(self):
        """Tags used by at least one published, non-featured project (the Home filters)."""
        return self.filter(projects__is_published=True, projects__is_featured=False).distinct()


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
    about_heading = models.CharField(
        max_length=80, blank=True, help_text='About page title, e.g. "Hi, I\'m Icaro."'
    )
    about_bio = models.TextField(blank=True)
    profile_photo = models.ImageField(
        upload_to=RandomFilename("site"), blank=True, validators=IMAGE_VALIDATORS
    )
    services_intro = models.CharField(
        max_length=200, blank=True, help_text='Line under "What I can build for you".'
    )
    contact_heading = models.CharField(
        max_length=80, blank=True, help_text='Contact card title, e.g. "Let\'s work together."'
    )
    contact_text = models.CharField(
        max_length=200, blank=True, help_text="Short line under the contact card title."
    )

    # Contact form
    notification_email = models.EmailField(
        blank=True,
        help_text="Where new contact form messages are emailed. Never shown on the site.",
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

    objects = TypeTagQuerySet.as_manager()

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
    slug = models.SlugField(
        max_length=140, unique=True, help_text="Web address: /projects/<slug>/. Filled from the title."
    )
    pitch = models.CharField(
        max_length=200, help_text="One plain-language line, shown on cards and under the title."
    )
    type_tags = models.ManyToManyField(TypeTag, related_name="projects", blank=True)
    role = models.CharField(max_length=80, blank=True, help_text='e.g. "Solo project"')
    period = models.CharField(max_length=40, blank=True, help_text='e.g. "Nov 2026"')

    # Media
    cover_image = models.ImageField(
        upload_to=RandomFilename("projects"),
        validators=IMAGE_VALIDATORS,
        help_text="Shown on cards and in link previews. Landscape, JPG, PNG or WebP, max 5 MB.",
    )
    video_url = models.URLField(
        blank=True,
        validators=[validate_video_url],
        help_text="YouTube or Loom link. Leave empty to hide the video box.",
    )

    # Links
    live_url = models.URLField("Live demo link", blank=True, help_text="Empty hides the button.")
    repo_url = models.URLField("GitHub repo link", blank=True, help_text="Empty hides the button.")

    # Content
    what_it_does = models.TextField(help_text="Plain language, for non-technical readers.")
    how_it_works = models.TextField(blank=True, help_text="Technical. Simple Markdown.")
    architecture_image = models.ImageField(
        upload_to=RandomFilename("projects"),
        blank=True,
        validators=IMAGE_VALIDATORS,
        help_text="Optional diagram shown under How it works.",
    )

    # Visibility and order
    is_featured = models.BooleanField(
        "Featured", default=False, help_text="Large card under Featured projects on Home."
    )
    is_published = models.BooleanField(
        "Published", default=True, help_text="Off hides the project everywhere on the site."
    )
    order = models.PositiveIntegerField(default=0, db_index=True)

    # SEO
    seo_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="Text shown by Google and link previews. Empty uses the pitch.",
    )

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("portfolio:project_detail", args=[self.slug])

    @property
    def video_embed_url(self):
        return embed_url(self.video_url)

    def next_project(self):
        """The next published project in admin order, wrapping to the first.

        Returns None when this is the only published project, so the page
        never links to itself. Ties in `order` are broken by id.
        """
        published = Project.objects.published().exclude(pk=self.pk).order_by("order", "pk")
        after = published.filter(Q(order__gt=self.order) | Q(order=self.order, pk__gt=self.pk))
        return after.first() or published.first()


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
        upload_to=RandomFilename("logos"),
        blank=True,
        validators=IMAGE_VALIDATORS,
        help_text="Square works best. Empty shows the first letter of the company.",
    )
    start_date = models.DateField(help_text="Only the month and year are shown.")
    end_date = models.DateField(null=True, blank=True, help_text="Empty means Present.")
    summary = models.CharField(max_length=300, help_text="One or two lines, always visible.")
    details = models.TextField(
        blank=True, help_text='Simple Markdown. "Show details" appears only when filled.'
    )
    techs = models.ManyToManyField(
        Tech, related_name="experiences", blank=True, help_text="Shown as chips on the card."
    )
    is_published = models.BooleanField("Published", default=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    objects = ExperienceQuerySet.as_manager()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.role} at {self.company}"

    @property
    def period_display(self):
        return date_range(self.start_date, self.end_date)


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

    @property
    def period_display(self):
        """The free-text label wins when filled, otherwise the date range."""
        return self.period_label or date_range(self.start_date, self.end_date)


class SkillGroup(TimeStampedModel):
    name = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=0, db_index=True)

    objects = SkillGroupQuerySet.as_manager()

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
