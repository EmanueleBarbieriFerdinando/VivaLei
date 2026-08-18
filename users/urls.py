from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import AccountView, CambioPasswordView, ModificaProfiloView, RegistrazioneView, UserLoginView


app_name = "users"


urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("registrazione/", RegistrazioneView.as_view(), name="registrazione"),
    path("account/", AccountView.as_view(), name="account"),
    path("account/modifica/", ModificaProfiloView.as_view(), name="modifica_profilo"),
    path("account/cambia-password/", CambioPasswordView.as_view(), name="cambia_password"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
