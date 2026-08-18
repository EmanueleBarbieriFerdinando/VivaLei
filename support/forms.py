from django import forms

from .models import Chat, Messaggio


class NuovaChatForm(forms.ModelForm):

    messaggio = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Scrivi il tuo messaggio..."
            }
        )
    )

    class Meta:
        model = Chat

        fields = [
            "categoria",
            "oggetto",
        ]

        widgets = {
            "categoria": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "oggetto": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Oggetto della richiesta"
                }
            ),
        }


class RispostaChatForm(forms.ModelForm):

    class Meta:
        model = Messaggio

        fields = [
            "testo",
        ]

        widgets = {
            "testo": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Scrivi una risposta..."
                }
            ),
        }