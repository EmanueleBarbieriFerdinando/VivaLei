from decimal import Decimal

from django.db import transaction

from products.models import Prodotto

from .models import RigaSessioneCheckout, SessioneCheckout


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