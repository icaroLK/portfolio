from django.urls import path

from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.home, name="home"),
    # Design check page; the view returns 404 unless DEBUG is on.
    path("styleguide/", views.styleguide, name="styleguide"),
]
