from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from contact.forms import ContactForm

from .models import (
    Education,
    Experience,
    Project,
    ProjectTech,
    Service,
    SiteSettings,
    Skill,
    SkillGroup,
    Tech,
    TypeTag,
)


def home(request):
    """Hero, featured projects and the archive grid, filtered by ?type=<slug>."""
    archive = Project.objects.archive().for_cards()
    active_type = request.GET.get("type", "")
    if active_type:
        # An unknown slug simply matches nothing, so the empty state shows.
        archive = archive.filter(type_tags__slug=active_type)

    context = {
        "featured_projects": Project.objects.featured().for_cards(),
        "archive_projects": archive,
        "filter_tags": TypeTag.objects.in_archive(),
        "active_type": active_type,
    }
    return render(request, "portfolio/home.html", context)


def project_detail(request, slug):
    """One project page. Missing or unpublished slugs get the styled 404."""
    project = get_object_or_404(Project.objects.published().for_detail(), slug=slug)
    context = {"project": project, "next_project": project.next_project()}
    return render(request, "portfolio/project_detail.html", context)


def about(request):
    return render_about(request, ContactForm())


def render_about(request, form, status=200):
    """The About page. Also used by the contact view to show a form with errors."""
    site = SiteSettings.load()
    # A turned-off section skips its query entirely.
    context = {
        "site": site,
        "form": form,
        "sent": request.GET.get("sent") == "1",
        "experiences": Experience.objects.for_about() if site.show_experience else [],
        "education": Education.objects.published() if site.show_education else [],
        "skill_groups": SkillGroup.objects.for_about() if site.show_skills else [],
        "services": Service.objects.published() if site.show_services else [],
    }
    return render(request, "portfolio/about.html", context, status=status)


def styleguide(request):
    """Every UI component on one page, for design checks. Only exists with DEBUG on."""
    if not settings.DEBUG:
        raise Http404
    # Sample chips use real rows (run seed_demo first), so nothing is hardcoded.
    context = {
        "sample_tags": TypeTag.objects.all()[:3],
        "sample_techs": Tech.objects.all()[:4],
        "sample_stack": ProjectTech.objects.select_related("tech")[:4],
        "sample_skills": Skill.objects.all()[:5],
    }
    return render(request, "portfolio/styleguide.html", context)


def preview_404(request):
    """The styled 404 page, viewable while DEBUG is on (Django shows its debug page otherwise)."""
    if not settings.DEBUG:
        raise Http404
    return render(request, "404.html", status=404)
