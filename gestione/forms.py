from django import forms
from tinymce.widgets import TinyMCE

from products.models import Categoria, ImmagineProdotto, Prodotto
from users.models import User


class GestioneUtenteForm(forms.ModelForm):
    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "email",
            "telefono",
            "is_active",
            "is_staff",
            "is_superuser",
        ]

        labels = {
            "first_name": "Nome",
            "last_name": "Cognome",
            "email": "Email",
            "telefono": "Telefono",
            "is_active": "Account attivo",
            "is_staff": "Membro dello staff",
            "is_superuser": "Superutente",
        }

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "is_staff": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "is_superuser": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(self, *args, puo_modificare_ruoli=False, **kwargs):
        super().__init__(*args, **kwargs)

        if not puo_modificare_ruoli:
            self.fields.pop("is_staff")
            self.fields.pop("is_superuser")


class ProdottoForm(forms.ModelForm):
    prezzo = forms.DecimalField(
        label="Prezzo",
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "0,00",
            }
        ),
    )

    descrizione = forms.CharField(
        label="Descrizione",
        required=False,
        widget=TinyMCE(
            attrs={
                "cols": 80,
                "rows": 18,
            },
            mce_attrs={
                "height": 420,
                "menubar": False,
                "plugins": "lists link",
                "toolbar": (
                    "undo redo | "
                    "blocks | "
                    "bold italic | "
                    "bullist numlist | "
                    "link | "
                    "removeformat"
                ),
                "block_formats": (
                    "Paragrafo=p;"
                    "Titolo=h2;"
                    "Sottotitolo=h3"
                ),
            },
        ),
    )

    class Meta:
        model = Prodotto

        fields = [
            "categoria",
            "nome",
            "descrizione",
            "prezzo",
            "quantita_disponibile",
            "immagine",
            "attivo",
        ]

        labels = {
            "categoria": "Categoria",
            "nome": "Nome prodotto",
            "quantita_disponibile": "Quantità disponibile",
            "immagine": "Immagine principale",
            "attivo": "Prodotto attivo",
        }

        widgets = {
            "categoria": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "nome": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nome del prodotto",
                }
            ),
            "quantita_disponibile": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                }
            ),
            "immagine": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            "attivo": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["categoria"].required = True

        self.fields["categoria"].queryset = (
            Categoria.objects
            .exclude(prefisso_sku__isnull=True)
            .exclude(prefisso_sku="")
            .order_by("nome")
        )

        self.fields["categoria"].empty_label = "Seleziona una categoria"


class ImmagineProdottoForm(forms.ModelForm):
    class Meta:
        model = ImmagineProdotto

        fields = [
            "immagine",
            "alt_text",
            "ordine",
            "principale",
        ]

        labels = {
            "immagine": "Immagine",
            "alt_text": "Descrizione immagine",
            "ordine": "Posizione",
            "principale": "Immagine principale",
        }

        widgets = {
            "immagine": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            "alt_text": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Esempio: Organizer VivaLei visto frontalmente",
                }
            ),
            "ordine": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                }
            ),
            "principale": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


class CategoriaForm(forms.ModelForm):
    prefisso_sku = forms.CharField(
        label="Prefisso SKU",
        min_length=2,
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-uppercase",
                "placeholder": "Esempio: CASA",
            }
        ),
    )

    class Meta:
        model = Categoria

        fields = [
            "nome",
            "mondo",
            "prefisso_sku",
        ]

        labels = {
            "nome": "Nome categoria",
            "mondo": "Mondo VivaLei",
        }

        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Esempio: Organizzazione",
                }
            ),
            "mondo": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()

        if Categoria.objects.filter(nome__iexact=nome).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                "Esiste già una categoria con questo nome."
            )

        return nome

    def clean_prefisso_sku(self):
        prefisso = self.cleaned_data["prefisso_sku"].strip().upper()

        if not prefisso.isalnum():
            raise forms.ValidationError(
                "Il prefisso può contenere soltanto lettere e numeri."
            )

        if Categoria.objects.filter(prefisso_sku__iexact=prefisso).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                "Questo prefisso SKU è già utilizzato."
            )

        return prefisso