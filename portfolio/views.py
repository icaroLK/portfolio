from django.shortcuts import render


def home(request):
    """Placeholder home page for Sprint 0. Sprint 3 builds the real one."""
    return render(request, "portfolio/home.html")
