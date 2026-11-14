from django.urls import path

from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.home, name="home"),
    path("projects/<slug:slug>/", views.project_detail, name="project_detail"),
    path("about/", views.about, name="about"),
    # Design check page; the view returns 404 unless DEBUG is on.
    path("styleguide/", views.styleguide, name="styleguide"),
    path("styleguide/404/", views.preview_404, name="preview_404"),
]
