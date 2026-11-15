from django.urls import path

from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.home, name="home"),
    path("projects/<slug:slug>/", views.project_detail, name="project_detail"),
    path("about/", views.about, name="about"),
    # Stable link for LinkedIn and applications: always the latest uploaded PDF.
    path("resume/", views.resume_download, name="resume"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("healthz/", views.healthz, name="healthz"),
    # Design check page; the view returns 404 unless DEBUG is on.
    path("styleguide/", views.styleguide, name="styleguide"),
    path("styleguide/404/", views.preview_404, name="preview_404"),
    path("styleguide/500/", views.preview_500, name="preview_500"),
]
