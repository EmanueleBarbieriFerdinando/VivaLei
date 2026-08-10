from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Categoria, Prodotto


MONDI_VIVALEI = {
    "casa": {
        "nome": "La mia casa",
        "eyebrow": "IL MONDO DELLA CASA",
        "titolo": "Più ordine, meno fatica.",
        "descrizione": (
            "Soluzioni pratiche per organizzare meglio gli spazi, "
            "semplificare le piccole attività quotidiane e rendere "
            "la casa ancora più piacevole da vivere."
        ),
    },
    "movimento": {
        "nome": "Tenersi in movimento",
        "eyebrow": "IL MONDO DEL MOVIMENTO",
        "titolo": "Muoversi, a modo tuo.",
        "descrizione": (
            "Prodotti semplici pensati per accompagnarti nelle attività "
            "di ogni giorno e aiutarti a mantenerti in movimento "
            "con maggiore comodità e secondo il tuo ritmo."
        ),
    },
    "tempo-per-me": {
        "nome": "Tempo per me",
        "eyebrow": "IL MONDO DEL BENESSERE",
        "titolo": "Un momento tutto per te.",
        "descrizione": (
            "Comfort, relax e piccoli gesti quotidiani per rallentare, "
            "prenderti cura di te e dedicare più tempo a ciò che "
            "ti fa stare bene."
        ),
    },
}


def lista_prodotti(request):
    ricerca = request.GET.get("q", "").strip()
    categoria_slug = request.GET.get("categoria", "")
    mondo_slug = request.GET.get("mondo", "")
    ordine = request.GET.get("ordine", "recenti")

    prodotti = Prodotto.objects.filter(attivo=True).select_related("categoria")

    if ricerca:
        prodotti = prodotti.filter(
            Q(nome__icontains=ricerca)
            | Q(descrizione__icontains=ricerca)
            | Q(sku__icontains=ricerca)
        )

    if mondo_slug in MONDI_VIVALEI:
        prodotti = prodotti.filter(categoria__mondo=mondo_slug)

    if categoria_slug:
        prodotti = prodotti.filter(categoria__slug=categoria_slug)

    ordinamenti = {
        "recenti": "-data_creazione",
        "nome": "nome",
        "prezzo_crescente": "prezzo",
        "prezzo_decrescente": "-prezzo",
    }

    prodotti = prodotti.order_by(
        ordinamenti.get(ordine, "-data_creazione")
    )

    paginator = Paginator(prodotti, 12)
    pagina = paginator.get_page(request.GET.get("page"))

    mondo = MONDI_VIVALEI.get(mondo_slug)

    categorie = Categoria.objects.order_by("nome")

    if mondo:
        categorie = categorie.filter(mondo=mondo_slug)

    context = {
        "prodotti": pagina,
        "pagina": pagina,
        "categorie": categorie,
        "ricerca": ricerca,
        "categoria_selezionata": categoria_slug,
        "mondo_selezionato": mondo_slug,
        "mondo": mondo,
        "ordine": ordine,
        "numero_risultati": paginator.count,
    }

    return render(
        request,
        "products/lista_prodotti.html",
        context,
    )


def ricerca_live(request):
    ricerca = request.GET.get("q", "").strip()

    prodotti = (
        Prodotto.objects
        .filter(attivo=True)
        .select_related("categoria")
    )

    if ricerca:
        prodotti = prodotti.filter(
            Q(nome__icontains=ricerca)
            | Q(descrizione__icontains=ricerca)
            | Q(sku__icontains=ricerca)
        )

    prodotti = prodotti.order_by("-data_creazione")[:6]

    risultati = [
        {
            "nome": prodotto.nome,
            "prezzo": f"{prodotto.prezzo:.2f}",
            "categoria": prodotto.categoria.nome if prodotto.categoria else "",
            "mondo": prodotto.categoria.mondo if prodotto.categoria else "",
            "url": prodotto.get_absolute_url(),
            "immagine": prodotto.immagine.url if prodotto.immagine else "",
        }
        for prodotto in prodotti
    ]

    return JsonResponse({
        "prodotti": risultati,
        "ricerca": ricerca,
    })


def dettaglio_prodotto(request, slug):
    prodotto = get_object_or_404(
        Prodotto.objects
        .select_related("categoria")
        .prefetch_related("immagini_extra"),
        slug=slug,
        attivo=True,
    )

    prodotti_correlati = (
        Prodotto.objects
        .filter(attivo=True, categoria=prodotto.categoria)
        .exclude(pk=prodotto.pk)
        .select_related("categoria")
        .order_by("-data_creazione")[:4]
    )

    context = {
        "prodotto": prodotto,
        "prodotti_correlati": prodotti_correlati,
    }

    return render(
        request,
        "products/dettaglio_prodotto.html",
        context,
    )