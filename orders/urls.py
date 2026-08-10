from django.urls import path

from . import views


app_name = "orders"


urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/<uuid:token>/", views.riepilogo_checkout, name="riepilogo_checkout"),
    path("checkout/<uuid:token>/pagamento/", views.crea_pagamento_checkout, name="crea_pagamento_checkout"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),

    path("miei/", views.miei_ordini, name="miei_ordini"),
    path("miei/<uuid:codice>/", views.dettaglio_mio_ordine, name="dettaglio_mio_ordine"),

    path("gestione/<uuid:codice>/", views.dettaglio_ordine, name="dettaglio"),
]