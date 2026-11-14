from django.conf import settings
from django.http import Http404
from django.shortcuts import render

from .models import ProjectTech, Skill, Tech, TypeTag


def home(request):
    """Placeholder home page. Sprint 3 builds the real one."""
    return render(request, "portfolio/home.html")


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
