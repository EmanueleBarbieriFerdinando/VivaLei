from django.contrib import admin

from .models import Categoria, ImmagineProdotto, Prodotto


class ImmagineProdottoInline(admin.TabularInline):
    model = ImmagineProdotto
    extra = 1

    fields = [
        "immagine",
        "alt_text",
        "ordine",
        "principale",
    ]


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = [
        "nome",
        "mondo",
        "prefisso_sku",
        "ultimo_progressivo_sku",
        "slug",
    ]

    list_filter = [
        "mondo",
    ]

    search_fields = [
        "nome",
        "prefisso_sku",
    ]

    readonly_fields = [
        "ultimo_progressivo_sku",
    ]

    prepopulated_fields = {
        "slug": ("nome",),
    }


@admin.register(Prodotto)
class ProdottoAdmin(admin.ModelAdmin):
    list_display = [
        "nome",
        "sku",
        "categoria",
        "prezzo",
        "prezzo_acquisto",
        "fornitore",
        "quantita_disponibile",
        "attivo",
    ]

    list_filter = [
        "attivo",
        "categoria",
        "data_creazione",
    ]

    search_fields = [
        "nome",
        "sku",
        "descrizione",
    ]

    list_editable = [
        "prezzo",
        "quantita_disponibile",
        "attivo",
    ]

    readonly_fields = [
        "sku",
        "data_creazione",
        "data_modifica",
    ]

    prepopulated_fields = {
        "slug": ("nome",),
    }

    inlines = [
        ImmagineProdottoInline,
    ]
