from django.conf import settings
from django.http import Http404
from django.shortcuts import render

from .models import Project, ProjectTech, Skill, Tech, TypeTag


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
