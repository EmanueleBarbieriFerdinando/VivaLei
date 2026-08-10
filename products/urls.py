from django.urls import path

from . import views


app_name = "products"


urlpatterns = [
    path("", views.lista_prodotti, name="lista_prodotti"),
    path("ricerca-live/", views.ricerca_live, name="ricerca_live"),
    path("<slug:slug>/", views.dettaglio_prodotto, name="dettaglio_prodotto"),
]