from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, UserCreationForm
from django.template.loader import render_to_string

from core.services.email_service import invia_email
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "nome@esempio.it",
            "autocomplete": "email",
        }),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Inserisci la password",
            "autocomplete": "current-password",
        }),
    )


class RegistrazioneForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "telefono", "password1", "password2"]
        labels = {
            "first_name": "Nome",
            "last_name": "Cognome",
            "email": "Email",
            "telefono": "Telefono",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for campo in self.fields.values():
            campo.widget.attrs["class"] = "form-control"

        self.fields["first_name"].widget.attrs["placeholder"] = "Inserisci il nome"
        self.fields["last_name"].widget.attrs["placeholder"] = "Inserisci il cognome"
        self.fields["email"].widget.attrs["placeholder"] = "nome@esempio.it"
        self.fields["telefono"].widget.attrs["placeholder"] = "Numero di telefono"
        self.fields["password1"].widget.attrs["placeholder"] = "Scegli una password"
        self.fields["password2"].widget.attrs["placeholder"] = "Ripeti la password"


class ProfiloForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "telefono"]
        labels = {
            "first_name": "Nome",
            "last_name": "Cognome",
            "email": "Email",
            "telefono": "Telefono",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "autocomplete": "tel"}),
        }


class CambioPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "old_password": "Inserisci la password attuale",
            "new_password1": "Scegli una nuova password",
            "new_password2": "Ripeti la nuova password",
        }
        for name, placeholder in placeholders.items():
            self.fields[name].widget.attrs.update({
                "class": "form-control",
                "placeholder": placeholder,
                "autocomplete": "current-password" if name == "old_password" else "new-password",
            })


class RecuperoPasswordForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "nome@esempio.it",
            "autocomplete": "email",
        })

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None):
        invia_email(
            destinatari=[to_email],
            oggetto=render_to_string(subject_template_name, context).strip(),
            corpo_testo=render_to_string(email_template_name, context),
            corpo_html=render_to_string(html_email_template_name, context),
        )
