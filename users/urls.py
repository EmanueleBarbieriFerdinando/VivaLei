from django.contrib.auth.views import LogoutView, PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView
from django.urls import path, reverse_lazy

from .forms import RecuperoPasswordForm
from .views import AccountView, CambioPasswordView, ModificaProfiloView, RegistrazioneView, UserLoginView


app_name = "users"


urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("password-reset/", PasswordResetView.as_view(template_name="users/password_reset.html", form_class=RecuperoPasswordForm, email_template_name="users/email/password_reset.txt", html_email_template_name="users/email/password_reset.html", subject_template_name="users/email/password_reset_subject.txt", success_url=reverse_lazy("users:password_reset_done")), name="password-reset"),
    path("password-reset/inviata/", PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(template_name="users/password_reset_confirm.html", success_url=reverse_lazy("users:password_reset_complete")), name="password_reset_confirm"),
    path("password-reset/completata/", PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html"), name="password_reset_complete"),
    path("registrazione/", RegistrazioneView.as_view(), name="registrazione"),
    path("account/", AccountView.as_view(), name="account"),
    path("account/modifica/", ModificaProfiloView.as_view(), name="modifica_profilo"),
    path("account/cambia-password/", CambioPasswordView.as_view(), name="cambia_password"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
