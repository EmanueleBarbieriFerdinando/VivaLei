from django.urls import path

from .views import (
    dashboard,
    gestione_ordini,
    gestione_prodotti,
    gestione_utenti,
    inserisci_categoria,
    inserisci_prodotto,
    modifica_prodotto,
    modifica_utente,
)


app_name = "gestione"


urlpatterns = [
    path("", dashboard, name="dashboard"),

    path("ordini/", gestione_ordini, name="ordini"),

    path("utenti/", gestione_utenti, name="utenti"),
    path("utenti/<int:utente_id>/modifica/", modifica_utente, name="modifica_utente"),

    path("prodotti/", gestione_prodotti, name="prodotti"),
    path("prodotti/nuovo/", inserisci_prodotto, name="inserisci_prodotto"),
    path("categorie/nuova/", inserisci_categoria, name="inserisci_categoria"),
    path("prodotti/<int:prodotto_id>/modifica/", modifica_prodotto, name="modifica_prodotto"),
]