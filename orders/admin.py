from django.contrib import admin

from .models import Ordine, RigaOrdine, RigaSessioneCheckout, SessioneCheckout


class RigaOrdineInline(admin.TabularInline):
    model = RigaOrdine
    extra = 0
    can_delete = False
    readonly_fields = ["prodotto", "nome_prodotto", "sku", "prezzo_unitario", "quantita", "totale"]

    @admin.display(description="Totale")
    def totale(self, riga):
        return riga.totale


@admin.register(Ordine)
class OrdineAdmin(admin.ModelAdmin):
    list_display = ["codice", "email", "stato", "stato_pagamento", "totale", "data_creazione"]
    list_filter = ["stato", "stato_pagamento", "data_creazione"]
    search_fields = ["codice", "email", "nome", "cognome", "stripe_checkout_session_id"]
    readonly_fields = ["codice", "stripe_checkout_session_id", "stripe_payment_intent_id", "data_creazione", "data_modifica", "data_pagamento"]
    inlines = [RigaOrdineInline]


class RigaSessioneCheckoutInline(admin.TabularInline):
    model = RigaSessioneCheckout
    extra = 0
    can_delete = False
    readonly_fields = ["prodotto", "nome_prodotto", "sku", "prezzo_unitario", "quantita", "totale"]


@admin.register(SessioneCheckout)
class SessioneCheckoutAdmin(admin.ModelAdmin):
    list_display = ["token", "email", "stato", "totale", "ordine", "data_creazione"]
    list_filter = ["stato", "data_creazione"]
    search_fields = ["token", "email", "stripe_checkout_session_id"]
    readonly_fields = ["token", "stripe_checkout_session_id", "ordine", "data_creazione", "data_modifica", "data_completamento"]
    inlines = [RigaSessioneCheckoutInline]