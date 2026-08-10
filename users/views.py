from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import LoginForm, RegistrazioneForm
from .models import User


class UserLoginView(LoginView):
    template_name = "users/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class RegistrazioneView(SuccessMessageMixin, CreateView):
    model = User
    form_class = RegistrazioneForm
    template_name = "users/registrazione.html"
    success_url = reverse_lazy("users:login")
    success_message = "Registrazione completata. Ora puoi accedere."


class AccountView(LoginRequiredMixin, TemplateView):
    template_name = "users/account.html"