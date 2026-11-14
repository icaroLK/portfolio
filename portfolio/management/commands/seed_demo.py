"""
python manage.py seed_demo

Fills the database with placeholder content so the site has something to show.
Safe to run many times: it only creates what is missing and never overwrites
anything you already edited in the admin.
"""

import io
from datetime import date

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from portfolio.models import (
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

# --- Placeholder content (from the V2 wireframes where they had real text) ---

SITE_SETTINGS = {
    "site_name": "Icaro Kucha",
    "headline": "I build websites, WhatsApp bots and automations that save businesses time.",
    "subheadline": "Icaro Kucha. Software engineer focused on AI automation, Python and Django.",
    "status_badge_text": "Open to work · Available for freelance",
    "about_heading": "Hi, I'm Icaro.",
    "about_bio": (
        "Placeholder intro. Write a few lines in your own voice: what you build, "
        "why you like it and how you work with people."
    ),
    "services_intro": (
        "For small businesses and teams that want to sell more or spend less time "
        "on repetitive work."
    ),
    "contact_heading": "Let's work together.",
    "contact_text": "Have a role or a project in mind? Send a message, or reach me directly.",
    "email": "hi@icarokucha.com",
    "github_url": "https://github.com/",
    "linkedin_url": "https://www.linkedin.com/",
    "location_line": "Curitiba, Brazil · Working remotely",
    "meta_description": (
        "Icaro Kucha builds websites, WhatsApp bots and automations with Python and Django."
    ),
}

TYPE_TAGS = ["Website", "System", "Bot", "Automation", "Computer Vision"]

TECHS = [
    "Python", "OpenCV", "Django", "PostgreSQL", "Docker", "Raspberry Pi",
    "n8n", "Evolution API", "OpenAI", "Telegram API",
]

PROJECTS = [
    {
        "title": "ParkEye",
        "pitch": "Shows parking lot owners how many spots are free and when the lot gets busy.",
        "tags": ["Computer Vision", "System"],
        "role": "Solo project",
        "period": "Nov 2026",
        "is_featured": True,
        "live_url": "https://example.com/",
        "repo_url": "https://example.com/",
        "what_it_does": (
            "Placeholder. Parking lot owners rarely know how full their lot is or when it "
            "gets busy. ParkEye watches the gate camera, counts cars and shows live "
            "occupancy on a simple dashboard."
        ),
        "how_it_works": (
            "Placeholder. How data flows from the camera to the dashboard, the main "
            "technical decisions and the challenges."
        ),
        "features": [
            "Counts cars entering and leaving through the gate camera",
            "Detects which spots are free or taken",
            "Dashboard with live occupancy and busiest hours",
            "Placeholder feature 4",
        ],
        "stack": [
            ("Python", "pipeline"),
            ("OpenCV", "car detection"),
            ("Django", "dashboard"),
            ("PostgreSQL", "data"),
            ("Docker", "deploy"),
        ],
    },
    {
        "title": "Match Replay System",
        "pitch": (
            "Players press a button at the field and get the last 30 seconds of the "
            "match on the website."
        ),
        "tags": ["System"],
        "role": "Client project",
        "period": "2026",
        "is_featured": True,
        "what_it_does": "Placeholder. Plain-language explanation of the replay system.",
        "features": [
            "One button at the field saves the last 30 seconds",
            "Clips appear on the website a few seconds later",
            "Placeholder feature 3",
        ],
        "stack": [
            ("Raspberry Pi", "recording"),
            ("Python", "video clips"),
            ("Django", "website"),
        ],
    },
    {
        "title": "Barbershop WhatsApp Bot",
        "pitch": "Customers book haircuts and get reminders on WhatsApp, without calling the shop.",
        "tags": ["Bot", "Automation"],
        "role": "Client project",
        "period": "2026",
        "is_featured": True,
        "what_it_does": "Placeholder. Plain-language explanation of the booking bot.",
        "features": [
            "Books haircuts through a WhatsApp chat",
            "Sends reminders before each appointment",
            "Placeholder feature 3",
        ],
        "stack": [
            ("n8n", "workflows"),
            ("Evolution API", "WhatsApp"),
            ("OpenAI", "conversation"),
        ],
    },
    {
        "title": "Telegram Transcription Bot",
        "pitch": "Send a voice message, get the text back in seconds.",
        "tags": ["Bot"],
        "role": "Solo project",
        "period": "2026",
        "is_featured": False,
        "what_it_does": "Placeholder. Plain-language explanation of the transcription bot.",
        "features": [],
        "stack": [
            ("Python", "bot"),
            ("Telegram API", "messages"),
        ],
    },
    {
        "title": "Landing Page Demo",
        "pitch": "Placeholder. A fast one-page site that turns visitors into customers.",
        "tags": ["Website"],
        "role": "Demo project",
        "period": "2026",
        "is_featured": False,
        "what_it_does": "Placeholder. Plain-language explanation of the landing page.",
        "features": [],
        "stack": [
            ("Django", "website"),
            ("Docker", "deploy"),
        ],
    },
    {
        "title": "Invoice Reminder Automation",
        "pitch": "Placeholder. Sends clients a friendly reminder before each invoice is due.",
        "tags": ["Automation"],
        "role": "Demo project",
        "period": "2026",
        "is_featured": False,
        "what_it_does": "Placeholder. Plain-language explanation of the automation.",
        "features": [],
        "stack": [
            ("n8n", "workflows"),
            ("OpenAI", "message text"),
        ],
    },
]

EXPERIENCES = [
    {
        "role": "Placeholder role",
        "company": "RADZ Group",
        "location": "Remote (US)",
        "start_date": date(2025, 3, 1),
        "end_date": date(2026, 6, 1),
        "summary": "Placeholder summary: one or two lines, always visible.",
        "details": (
            "Placeholder description of the company and what you were responsible for.\n\n"
            "- Built X automation that did Y\n"
            "- Set up self-hosted infrastructure for Z\n"
            "- Integrated AI APIs into client workflows"
        ),
        "techs": ["n8n", "Python"],
    },
    {
        "role": "Freelance developer",
        "company": "Freelance clients",
        "location": "Curitiba, Brazil",
        "start_date": date(2024, 1, 1),
        "end_date": None,
        "summary": "Placeholder summary: one or two lines, always visible.",
        "details": "",  # empty on purpose: no "Show details" toggle for this one
        "techs": ["Django"],
    },
]

EDUCATION = [
    {
        "degree": "B.Sc. Software Engineering",
        "school": "PUCPR",
        "city": "Curitiba, Brazil",
        "start_date": date(2023, 2, 1),
        "end_date": date(2027, 6, 30),
        "period_label": "",
    },
    {
        "degree": "Erasmus exchange semester",
        "school": "AGH University",
        "city": "Kraków, Poland",
        "start_date": date(2026, 2, 1),
        "end_date": date(2026, 7, 1),
        "period_label": "Erasmus semester, 2026",
    },
]

SKILL_GROUPS = {
    "Automation & AI": ["n8n", "OpenAI API", "Anthropic API", "Gemini API", "AI agents"],
    "Backend": ["Python", "Django", "REST APIs"],
    "Computer Vision": ["OpenCV"],
    "Infra & tools": ["Docker", "Linux / VPS", "Git"],
}

SERVICES = [
    (
        "Websites & landing pages",
        "A fast, good-looking site that shows what you do and brings in customers.",
    ),
    (
        "Business systems",
        "Booking, client areas, dashboards and admin panels built around how you work.",
    ),
    (
        "WhatsApp bots & automations",
        "Answer customers, take bookings and handle routine tasks automatically.",
    ),
]


def placeholder_image(label, size=(1600, 1000)):
    """A plain gray PNG with a label in the middle, ready to save in an ImageField."""
    image = Image.new("RGB", size, "#EDEDEA")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=max(size) // 20)
    draw.text((size[0] / 2, size[1] / 2), label, fill="#9A9A96", font=font, anchor="mm")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{slugify(label)}.png")


class Command(BaseCommand):
    help = "Fill the database with placeholder content. Safe to run more than once."

    @transaction.atomic  # all or nothing: a crash halfway leaves the database untouched
    def handle(self, *args, **options):
        self.seed_site_settings()
        tags = self.seed_type_tags()
        techs = self.seed_techs()
        self.seed_projects(tags, techs)
        self.seed_experiences(techs)
        self.seed_education()
        self.seed_skills()
        self.seed_services()
        self.stdout.write(self.style.SUCCESS("Demo content is ready."))

    def seed_site_settings(self):
        settings = SiteSettings.load()
        # Only fill empty fields, so your own edits survive a second run.
        for field, value in SITE_SETTINGS.items():
            if not getattr(settings, field):
                setattr(settings, field, value)
        if not settings.profile_photo:
            settings.profile_photo = placeholder_image("Photo", size=(600, 600))
        if not settings.og_image:
            settings.og_image = placeholder_image("Share image", size=(1200, 630))
        settings.save()

    def seed_type_tags(self):
        tags = {}
        for order, name in enumerate(TYPE_TAGS):
            tags[name], _ = TypeTag.objects.get_or_create(
                slug=slugify(name), defaults={"name": name, "order": order}
            )
        return tags

    def seed_techs(self):
        techs = {}
        for name in TECHS:
            techs[name], _ = Tech.objects.get_or_create(
                slug=slugify(name), defaults={"name": name}
            )
        return techs

    def seed_projects(self, tags, techs):
        for order, data in enumerate(PROJECTS):
            project, created = Project.objects.get_or_create(
                slug=slugify(data["title"]),
                defaults={
                    "title": data["title"],
                    "pitch": data["pitch"],
                    "role": data["role"],
                    "period": data["period"],
                    "what_it_does": data["what_it_does"],
                    "how_it_works": data.get("how_it_works", ""),
                    "live_url": data.get("live_url", ""),
                    "repo_url": data.get("repo_url", ""),
                    "is_featured": data["is_featured"],
                    "order": order,
                    "cover_image": placeholder_image(data["title"]),
                },
            )
            if not created:
                continue  # already there: leave it exactly as you edited it

            project.type_tags.set([tags[name] for name in data["tags"]])
            for i, text in enumerate(data["features"]):
                ProjectFeature.objects.create(project=project, text=text, order=i)
            for i, (tech_name, purpose) in enumerate(data["stack"]):
                ProjectTech.objects.create(
                    project=project, tech=techs[tech_name], purpose=purpose, order=i
                )
            for i in range(3):
                ProjectImage.objects.create(
                    project=project,
                    image=placeholder_image(f"Image {i + 1}", size=(1600, 1000)),
                    caption=f"Placeholder image {i + 1}",
                    order=i,
                )

    def seed_experiences(self, techs):
        for order, data in enumerate(EXPERIENCES):
            fields = {key: value for key, value in data.items() if key != "techs"}
            experience, created = Experience.objects.get_or_create(
                role=data["role"],
                company=data["company"],
                defaults={**fields, "order": order},
            )
            if created:
                experience.techs.set([techs[name] for name in data["techs"]])

    def seed_education(self):
        for order, data in enumerate(EDUCATION):
            Education.objects.get_or_create(
                degree=data["degree"],
                school=data["school"],
                defaults={**data, "order": order},
            )

    def seed_skills(self):
        for order, (group_name, skills) in enumerate(SKILL_GROUPS.items()):
            group, created = SkillGroup.objects.get_or_create(
                name=group_name, defaults={"order": order}
            )
            if created:
                for i, name in enumerate(skills):
                    Skill.objects.create(group=group, name=name, order=i)

    def seed_services(self):
        for order, (title, description) in enumerate(SERVICES):
            Service.objects.get_or_create(
                title=title, defaults={"description": description, "order": order}
            )
