from django.urls import path
from .views import aggiungi_al_carrello, aggiorna_carrello, dettaglio_carrello, rimuovi_dal_carrello

app_name = "carrello"

urlpatterns = [
    path("", dettaglio_carrello, name="dettaglio"),
    path("aggiungi/<int:prodotto_id>/", aggiungi_al_carrello, name="aggiungi"),
    path("aggiorna/<int:prodotto_id>/", aggiorna_carrello, name="aggiorna"),
    path("rimuovi/<int:prodotto_id>/", rimuovi_dal_carrello, name="rimuovi"),
]