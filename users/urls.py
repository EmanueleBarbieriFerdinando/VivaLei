from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import AccountView, RegistrazioneView, UserLoginView


app_name = "users"


urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("registrazione/", RegistrazioneView.as_view(), name="registrazione"),
    path("account/", AccountView.as_view(), name="account"),
    path("logout/", LogoutView.as_view(), name="logout"),
]