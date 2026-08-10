from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from carrello.carrello import Carrello
from django.core.exceptions import PermissionDenied

from .forms import CheckoutForm
from .models import Ordine, SessioneCheckout, RigaOrdine
from .services import crea_sessione_checkout_da_carrello
import stripe

from django.conf import settings
from django.urls import reverse
from django.views.decorators.http import require_POST

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from stripe import SignatureVerificationError
import uuid


def recupera_ordine_pagato_da_stripe(sessione_checkout):
    """Recupera un checkout pagato quando il webhook non e ancora arrivato."""
    if not settings.STRIPE_SECRET_KEY or not sessione_checkout.stripe_checkout_session_id:
        return None

    stripe.api_key = settings.STRIPE_SECRET_KEY
    sessione_stripe = stripe.checkout.Session.retrieve(
        sessione_checkout.stripe_checkout_session_id
    )

    if sessione_stripe.status != "complete" or sessione_stripe.payment_status != "paid":
        return None

    return conferma_pagamento_stripe(sessione_stripe)

@login_required(login_url="users:login")
def checkout(request):
    carrello = Carrello(request)

    if len(carrello) == 0:
        messages.warning(request, "Il carrello è vuoto.")
        return redirect("products:lista_prodotti")

    righe_carrello = list(carrello)
    subtotale_carrello = sum((voce["prodotto"].prezzo * int(voce["quantita"]) for voce in righe_carrello), Decimal("0.00"))

    if request.method == "POST":
        form = CheckoutForm(request.POST)

        if form.is_valid():
            try:
                sessione = crea_sessione_checkout_da_carrello(utente=request.user, carrello=carrello, dati_checkout=form.cleaned_data)
            except ValueError as errore:
                messages.error(request, str(errore))
            else:
                return redirect("orders:riepilogo_checkout", token=sessione.token)
    else:
        form = CheckoutForm(initial={
            "checkout_token": uuid.uuid4(),
            "nome": request.user.first_name,
            "cognome": request.user.last_name,
            "email": request.user.email,
            "telefono": request.user.telefono,
            "paese": "Italia",
        })

    context = {
        "form": form,
        "righe_carrello": righe_carrello,
        "subtotale_carrello": subtotale_carrello,
        "costo_spedizione": Decimal("0.00"),
        "totale_carrello": subtotale_carrello,
    }

    return render(request, "orders/checkout.html", context)


@login_required(login_url="users:login")
@login_required(login_url="users:login")
def dettaglio_ordine(request, codice):
    if not request.user.is_superuser:
        raise PermissionDenied

    ordine = get_object_or_404(Ordine.objects.prefetch_related("righe"), codice=codice)

    return render(request, "orders/dettaglio_ordine.html", {"ordine": ordine})

@login_required(login_url="users:login")
def miei_ordini(request):
    ordini = Ordine.objects.filter(utente=request.user).prefetch_related("righe").order_by("-data_creazione")

    return render(request, "orders/miei_ordini.html", {"ordini": ordini})


@login_required(login_url="users:login")
def dettaglio_mio_ordine(request, codice):
    ordine = get_object_or_404(
        Ordine.objects.prefetch_related("righe"),
        codice=codice,
        utente=request.user,
    )

    return render(request, "orders/dettaglio_mio_ordine.html", {"ordine": ordine})

@login_required(login_url="users:login")
@require_POST
def crea_pagamento_checkout(request, token):
    sessione_checkout = get_object_or_404(SessioneCheckout.objects.prefetch_related("righe"), token=token, utente=request.user)

    if sessione_checkout.ordine_id:
        return redirect("orders:dettaglio_mio_ordine", codice=ordine.codice)

    if sessione_checkout.stato != SessioneCheckout.Stato.APERTA:
        messages.error(request, "Questa sessione checkout non può più essere pagata.")
        return redirect("orders:riepilogo_checkout", token=sessione_checkout.token)

    if not settings.STRIPE_SECRET_KEY:
        messages.error(request, "La chiave segreta Stripe non è configurata.")
        return redirect("orders:riepilogo_checkout", token=sessione_checkout.token)

    stripe.api_key = settings.STRIPE_SECRET_KEY

    if sessione_checkout.stripe_checkout_session_id:
        try:
            sessione_stripe_esistente = stripe.checkout.Session.retrieve(sessione_checkout.stripe_checkout_session_id)

            if sessione_stripe_esistente.status == "open" and sessione_stripe_esistente.url:
                return redirect(sessione_stripe_esistente.url)

            if sessione_stripe_esistente.status == "complete":
                ordine = recupera_ordine_pagato_da_stripe(sessione_checkout)
                if ordine:
                    Carrello(request).svuota()
                    messages.success(request, "Pagamento confermato. Il tuo ordine è stato ricevuto correttamente.")
                    return redirect("orders:dettaglio", codice=ordine.codice)

                messages.info(request, "Stripe non ha ancora confermato il pagamento.")
                return redirect("orders:riepilogo_checkout", token=sessione_checkout.token)
        except (stripe.StripeError, SessioneCheckout.DoesNotExist, ValueError) as errore:
            print(f"Errore recupero sessione Stripe: {errore}")

    elementi_stripe = []

    for riga in sessione_checkout.righe.all():
        elementi_stripe.append({
            "price_data": {
                "currency": sessione_checkout.valuta.lower(),
                "product_data": {
                    "name": riga.nome_prodotto,
                    "description": f"SKU: {riga.sku}",
                },
                "unit_amount": int(riga.prezzo_unitario * 100),
            },
            "quantity": riga.quantita,
        })

    if sessione_checkout.costo_spedizione > 0:
        elementi_stripe.append({
            "price_data": {
                "currency": sessione_checkout.valuta.lower(),
                "product_data": {
                    "name": "Spedizione",
                },
                "unit_amount": int(sessione_checkout.costo_spedizione * 100),
            },
            "quantity": 1,
        })

    url_riepilogo = request.build_absolute_uri(reverse("orders:riepilogo_checkout", kwargs={"token": sessione_checkout.token}))
    url_successo = f"{url_riepilogo}?checkout=success&session_id={{CHECKOUT_SESSION_ID}}"
    url_annullamento = f"{url_riepilogo}?checkout=cancelled"

    try:
        sessione_stripe = stripe.checkout.Session.create(
            mode="payment",
            line_items=elementi_stripe,
            customer_email=sessione_checkout.email,
            client_reference_id=str(sessione_checkout.token),
            metadata={
                "sessione_checkout_id": str(sessione_checkout.pk),
                "sessione_checkout_token": str(sessione_checkout.token),
            },
            payment_intent_data={
                "metadata": {
                    "sessione_checkout_id": str(sessione_checkout.pk),
                    "sessione_checkout_token": str(sessione_checkout.token),
                },
            },
            success_url=url_successo,
            cancel_url=url_annullamento,
            idempotency_key=f"checkout-{sessione_checkout.token}",
        )
    except stripe.StripeError as errore:
        print(f"Errore Stripe: {errore}")
        messages.error(request, "Non è stato possibile avviare il pagamento. Riprova.")
        return redirect("orders:riepilogo_checkout", token=sessione_checkout.token)

    sessione_checkout.stripe_checkout_session_id = sessione_stripe.id
    sessione_checkout.save(update_fields=["stripe_checkout_session_id", "data_modifica"])

    return redirect(sessione_stripe.url)

@transaction.atomic
def conferma_pagamento_stripe(sessione_stripe):
    sessione_checkout = SessioneCheckout.objects.select_for_update().prefetch_related("righe").get(stripe_checkout_session_id=sessione_stripe.id)

    if sessione_checkout.ordine_id:
        return sessione_checkout.ordine

    totale_atteso = int(sessione_checkout.totale * 100)

    if sessione_stripe.payment_status != "paid":
        raise ValueError("La sessione Stripe non risulta pagata.")

    if sessione_stripe.amount_total != totale_atteso:
        raise ValueError("Il totale ricevuto da Stripe non coincide con quello del checkout.")

    if sessione_stripe.currency.lower() != sessione_checkout.valuta.lower():
        raise ValueError("La valuta ricevuta da Stripe non coincide con quella del checkout.")

    ordine = Ordine.objects.create(
        utente=sessione_checkout.utente,
        stato=Ordine.Stato.PAGATO,
        stato_pagamento=Ordine.StatoPagamento.PAGATO,
        nome=sessione_checkout.nome,
        cognome=sessione_checkout.cognome,
        email=sessione_checkout.email,
        telefono=sessione_checkout.telefono,
        indirizzo=sessione_checkout.indirizzo,
        numero_civico=sessione_checkout.numero_civico,
        cap=sessione_checkout.cap,
        citta=sessione_checkout.citta,
        provincia=sessione_checkout.provincia,
        paese=sessione_checkout.paese,
        note=sessione_checkout.note,
        subtotale=sessione_checkout.subtotale,
        costo_spedizione=sessione_checkout.costo_spedizione,
        totale=sessione_checkout.totale,
        valuta=sessione_checkout.valuta,
        stripe_checkout_session_id=sessione_stripe.id,
        stripe_payment_intent_id=sessione_stripe.payment_intent or "",
        data_pagamento=timezone.now(),
    )

    RigaOrdine.objects.bulk_create([
        RigaOrdine(
            ordine=ordine,
            prodotto=riga.prodotto,
            nome_prodotto=riga.nome_prodotto,
            sku=riga.sku,
            prezzo_unitario=riga.prezzo_unitario,
            quantita=riga.quantita,
        )
        for riga in sessione_checkout.righe.all()
    ])

    sessione_checkout.stato = SessioneCheckout.Stato.COMPLETATA
    sessione_checkout.ordine = ordine
    sessione_checkout.data_completamento = timezone.now()
    sessione_checkout.save(update_fields=["stato", "ordine", "data_completamento", "data_modifica"])

    return ordine

@csrf_exempt
@require_POST
def stripe_webhook(request):
    firma_stripe = request.headers.get("Stripe-Signature")

    try:
        evento = stripe.Webhook.construct_event(request.body, firma_stripe, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        return HttpResponse("Payload non valido", status=400)
    except SignatureVerificationError:
        return HttpResponse("Firma Stripe non valida", status=400)

    if evento.type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        try:
            conferma_pagamento_stripe(evento.data.object)
        except (SessioneCheckout.DoesNotExist, ValueError) as errore:
            print(f"Errore webhook Stripe: {errore}")
            return HttpResponse("Checkout non aggiornato", status=400)

    return HttpResponse(status=200)

@login_required(login_url="users:login")
def riepilogo_checkout(request, token):
    sessione = get_object_or_404(SessioneCheckout.objects.prefetch_related("righe", "ordine"), token=token, utente=request.user)

    if sessione.ordine_id:
        Carrello(request).svuota()
        return redirect("orders:dettaglio", codice=sessione.ordine.codice)

    if request.GET.get("checkout") == "success":
        try:
            ordine = recupera_ordine_pagato_da_stripe(sessione)
        except (stripe.StripeError, SessioneCheckout.DoesNotExist, ValueError) as errore:
            print(f"Errore verifica pagamento Stripe: {errore}")
        else:
            if ordine:
                Carrello(request).svuota()
                messages.success(request, "Pagamento confermato. Il tuo ordine è stato ricevuto correttamente.")
                return redirect("orders:dettaglio", codice=ordine.codice)

    return render(request, "orders/riepilogo_checkout.html", {"sessione": sessione})
