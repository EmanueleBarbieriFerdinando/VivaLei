from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
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