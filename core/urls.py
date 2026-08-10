from django.urls import path

from .views import home, chi_siamo


app_name = "core"


urlpatterns = [
    path("", home, name="home"),
    path("chi-siamo/", chi_siamo, name="chi_siamo"),
]