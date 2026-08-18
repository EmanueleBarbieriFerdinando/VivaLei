from django.urls import path

from .views import (
    crea_chat,
    mie_richieste,
    dettaglio_chat,
    chiudi_chat,
)


app_name = "support"


urlpatterns = [
    path(
        "nuova/",
        crea_chat,
        name="crea_chat"
    ),

    path(
        "mie-richieste/",
        mie_richieste,
        name="mie_richieste"
    ),

    path(
        "<int:chat_id>/",
        dettaglio_chat,
        name="dettaglio_chat"
    ),

    path(
        "<int:chat_id>/chiudi/",
        chiudi_chat,
        name="chiudi_chat"
    ),
]