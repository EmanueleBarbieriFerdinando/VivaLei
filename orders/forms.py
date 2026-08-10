from django import forms

from .models import SessioneCheckout

class CheckoutForm(forms.ModelForm):
    checkout_token = forms.UUIDField(widget=forms.HiddenInput())

    accetta_condizioni = forms.BooleanField(
        label="Accetto le condizioni di vendita",
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = SessioneCheckout

        fields = [
            "nome",
            "cognome",
            "email",
            "telefono",
            "indirizzo",
            "numero_civico",
            "cap",
            "citta",
            "provincia",
            "paese",
            "note",
        ]

        labels = {
            "nome": "Nome",
            "cognome": "Cognome",
            "email": "Email",
            "telefono": "Telefono",
            "indirizzo": "Indirizzo",
            "numero_civico": "Numero civico",
            "cap": "CAP",
            "citta": "Città",
            "provincia": "Provincia",
            "paese": "Paese",
            "note": "Note per la consegna",
        }

        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "cognome": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "indirizzo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Via Roma"}),
            "numero_civico": forms.TextInput(attrs={"class": "form-control", "placeholder": "10/A"}),
            "cap": forms.TextInput(attrs={"class": "form-control"}),
            "citta": forms.TextInput(attrs={"class": "form-control"}),
            "provincia": forms.TextInput(attrs={"class": "form-control", "placeholder": "RE"}),
            "paese": forms.TextInput(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }