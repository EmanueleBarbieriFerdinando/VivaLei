from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from products.models import Prodotto
from .carrello import Carrello
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme

def dettaglio_carrello(request):
    carrello = Carrello(request)

    context = {
        "carrello": carrello,
    }

    return render(request, "carrello/dettaglio.html", context)


@require_POST
def aggiungi_al_carrello(request, prodotto_id):
    prodotto = get_object_or_404(Prodotto, id=prodotto_id, attivo=True)

    try:
        quantita = int(request.POST.get("quantita", 1))
    except (TypeError, ValueError):
        quantita = 1

    if quantita < 1:
        messages.error(request, "La quantità selezionata non è valida.")
        return redirect("products:dettaglio_prodotto", slug=prodotto.slug)

    if prodotto.quantita_disponibile == 0:
        messages.error(request, "Il prodotto è esaurito.")
        return redirect("products:dettaglio_prodotto", slug=prodotto.slug)

    quantita_inserita = Carrello(request).aggiungi(prodotto, quantita)

    if quantita_inserita < quantita:
        messages.warning(request, f"Sono disponibili soltanto {prodotto.quantita_disponibile} unità.")

    messages.success(request, f"{prodotto.nome} è stato aggiunto al carrello.")

    pagina_successiva = request.POST.get("next", "")

    if pagina_successiva and url_has_allowed_host_and_scheme(pagina_successiva, allowed_hosts={request.get_host()},
                                                             require_https=request.is_secure()):
        return redirect(pagina_successiva)

    return redirect("products:dettaglio_prodotto", slug=prodotto.slug)


@require_POST
def aggiorna_carrello(request, prodotto_id):
    prodotto = get_object_or_404(Prodotto, id=prodotto_id)
    carrello = Carrello(request)

    try:
        quantita = int(request.POST.get("quantita", 1))
    except (TypeError, ValueError):
        return JsonResponse({
            "ok": False,
            "messaggio": "Quantità non valida.",
        }, status=400)

    if quantita < 0:
        return JsonResponse({
            "ok": False,
            "messaggio": "La quantità non può essere negativa.",
        }, status=400)

    if quantita == 0:
        carrello.rimuovi(prodotto)

        return JsonResponse({
            "ok": True,
            "rimosso": True,
            "numero_prodotti": len(carrello),
            "totale_carrello": str(carrello.totale()),
        })

    quantita_inserita = carrello.aggiungi(prodotto, quantita, sostituisci=True)
    totale_riga = prodotto.prezzo * quantita_inserita

    if quantita_inserita < quantita:
        messaggio = f"Disponibili solamente {quantita_inserita} pezzi."
    else:
        messaggio = "Carrello aggiornato."

    return JsonResponse({
        "ok": True,
        "rimosso": False,
        "quantita": quantita_inserita,
        "totale_riga": str(totale_riga),
        "totale_carrello": str(carrello.totale()),
        "numero_prodotti": len(carrello),
        "messaggio": messaggio,
    })


@require_POST
def rimuovi_dal_carrello(request, prodotto_id):
    prodotto = get_object_or_404(Prodotto, id=prodotto_id)
    Carrello(request).rimuovi(prodotto)

    messages.success(request, f"{prodotto.nome} è stato rimosso dal carrello.")

    return redirect("carrello:dettaglio")