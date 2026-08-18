from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView

from .forms import CambioPasswordForm, LoginForm, ProfiloForm, RegistrazioneForm
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("profilo_form", ProfiloForm(instance=self.request.user))
        context.setdefault("password_form", CambioPasswordForm(user=self.request.user))
        return context


class ModificaProfiloView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfiloForm
    template_name = "users/account.html"
    success_url = reverse_lazy("users:account")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, "I tuoi dati sono stati aggiornati correttamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profilo_form"] = context["form"]
        context.setdefault("password_form", CambioPasswordForm(user=self.request.user))
        context["profilo_aperto"] = True
        return context


class CambioPasswordView(LoginRequiredMixin, PasswordChangeView):
    form_class = CambioPasswordForm
    template_name = "users/account.html"
    success_url = reverse_lazy("users:account")

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, "La password è stata modificata correttamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["password_form"] = context["form"]
        context.setdefault("profilo_form", ProfiloForm(instance=self.request.user))
        context["password_aperto"] = True
        return context
