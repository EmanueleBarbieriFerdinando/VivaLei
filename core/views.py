from django.shortcuts import render

from products.models import Categoria, Prodotto


def chi_siamo(request):
    return render(request, "core/chi_siamo.html")


def home(request):
    prodotti_casa = (
        Prodotto.objects
        .filter(
            attivo=True,
            categoria__mondo=Categoria.Mondo.CASA,
        )
        .select_related("categoria")
        .order_by("-data_creazione")[:4]
    )

    prodotti_movimento = (
        Prodotto.objects
        .filter(
            attivo=True,
            categoria__mondo=Categoria.Mondo.MOVIMENTO,
        )
        .select_related("categoria")
        .order_by("-data_creazione")[:4]
    )

    prodotti_tempo = (
        Prodotto.objects
        .filter(
            attivo=True,
            categoria__mondo=Categoria.Mondo.TEMPO_PER_ME,
        )
        .select_related("categoria")
        .order_by("-data_creazione")[:4]
    )

    context = {
        "prodotti_casa": prodotti_casa,
        "prodotti_movimento": prodotti_movimento,
        "prodotti_tempo": prodotti_tempo,
    }

    return render(
        request,
        "core/home.html",
        context,
    )