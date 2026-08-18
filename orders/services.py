from decimal import Decimal

from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from core.services.email_service import invia_email
from products.models import Prodotto

from .models import NotificaOrdine, RigaSessioneCheckout, SessioneCheckout


def invia_email_ordine_ricevuto(notifica_id):
    """Invia e registra la conferma dell'ordine senza bloccare il checkout."""
    notifica = NotificaOrdine.objects.select_related("ordine").prefetch_related("ordine__righe").get(pk=notifica_id)
    ordine = notifica.ordine
    contesto = {"ordine": ordine}

    try:
        invia_email(
            destinatari=[notifica.destinatario],
            oggetto=f"VivaLei - Ordine {ordine.codice} ricevuto",
            corpo_testo=render_to_string("orders/email/conferma_ordine.txt", contesto),
            corpo_html=render_to_string("orders/email/conferma_ordine.html", contesto),
        )
    except Exception as errore:
        notifica.stato = NotificaOrdine.Stato.ERRORE
        notifica.errore = str(errore)[:2000]
        notifica.save(update_fields=["stato", "errore"])
        return False

    notifica.stato = NotificaOrdine.Stato.INVIATA
    notifica.data_invio = timezone.now()
    notifica.errore = ""
    notifica.save(update_fields=["stato", "data_invio", "errore"])
    return True


@transaction.atomic
def crea_sessione_checkout_da_carrello(*, utente, carrello, dati_checkout):
    token = dati_checkout["checkout_token"]

    sessione_esistente = SessioneCheckout.objects.select_for_update().filter(token=token).first()

    if sessione_esistente:
        if sessione_esistente.utente_id != utente.id:
            raise ValueError("Questa sessione checkout non appartiene all'utente corrente.")

        return sessione_esistente

    righe_da_creare = []
    subtotale = Decimal("0.00")

    for voce in carrello:
        prodotto = Prodotto.objects.select_for_update().get(pk=voce["prodotto"].pk)
        quantita = int(voce["quantita"])

        if not prodotto.attivo:
            raise ValueError(f"Il prodotto «{prodotto.nome}» non è più disponibile.")

        if quantita < 1:
            raise ValueError(f"La quantità indicata per «{prodotto.nome}» non è valida.")

        if prodotto.quantita_disponibile < quantita:
            raise ValueError(f"Per «{prodotto.nome}» sono disponibili soltanto {prodotto.quantita_disponibile} pezzi.")

        subtotale += prodotto.prezzo * quantita

        righe_da_creare.append({
            "prodotto": prodotto,
            "nome_prodotto": prodotto.nome,
            "sku": prodotto.sku,
            "prezzo_unitario": prodotto.prezzo,
            "quantita": quantita,
        })

    if not righe_da_creare:
        raise ValueError("Il carrello è vuoto.")

    costo_spedizione = Decimal("0.00")
    totale = subtotale + costo_spedizione

    sessione = SessioneCheckout.objects.create(
        token=token,
        utente=utente,
        nome=dati_checkout["nome"],
        cognome=dati_checkout["cognome"],
        email=dati_checkout["email"],
        telefono=dati_checkout["telefono"],
        indirizzo=dati_checkout["indirizzo"],
        numero_civico=dati_checkout["numero_civico"],
        cap=dati_checkout["cap"],
        citta=dati_checkout["citta"],
        provincia=dati_checkout["provincia"],
        paese=dati_checkout["paese"],
        note=dati_checkout["note"],
        subtotale=subtotale,
        costo_spedizione=costo_spedizione,
        totale=totale,
    )

    RigaSessioneCheckout.objects.bulk_create([
        RigaSessioneCheckout(
            sessione=sessione,
            prodotto=riga["prodotto"],
            nome_prodotto=riga["nome_prodotto"],
            sku=riga["sku"],
            prezzo_unitario=riga["prezzo_unitario"],
            quantita=riga["quantita"],
        )
        for riga in righe_da_creare
    ])

    return sessione
