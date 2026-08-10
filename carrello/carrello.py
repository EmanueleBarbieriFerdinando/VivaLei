from decimal import Decimal
from products.models import Prodotto


class Carrello:
    SESSION_KEY = "carrello"

    def __init__(self, request):
        self.session = request.session
        self.dati = self.session.get(self.SESSION_KEY, {})

    def aggiungi(self, prodotto, quantita=1, sostituisci=False):
        prodotto_id = str(prodotto.id)
        quantita_attuale = self.dati.get(prodotto_id, {}).get("quantita", 0)

        if sostituisci:
            nuova_quantita = quantita
        else:
            nuova_quantita = quantita_attuale + quantita

        nuova_quantita = min(nuova_quantita, prodotto.quantita_disponibile)

        if nuova_quantita <= 0:
            self.rimuovi(prodotto)
            return 0

        self.dati[prodotto_id] = {
            "quantita": nuova_quantita,
        }

        self.salva()
        return nuova_quantita

    def rimuovi(self, prodotto):
        prodotto_id = str(prodotto.id)

        if prodotto_id in self.dati:
            del self.dati[prodotto_id]
            self.salva()

    def salva(self):
        self.session[self.SESSION_KEY] = self.dati
        self.session.modified = True

    def svuota(self):
        self.session[self.SESSION_KEY] = {}
        self.session.modified = True
        self.dati = {}

    def __iter__(self):
        prodotti = Prodotto.objects.filter(id__in=self.dati.keys()).select_related("categoria")

        for prodotto in prodotti:
            elemento = self.dati[str(prodotto.id)].copy()
            elemento["prodotto"] = prodotto
            elemento["prezzo"] = prodotto.prezzo
            elemento["totale"] = prodotto.prezzo * elemento["quantita"]

            yield elemento

    def __len__(self):
        return sum(elemento["quantita"] for elemento in self.dati.values())

    def totale(self):
        totale = Decimal("0.00")

        for elemento in self:
            totale += elemento["totale"]

        return totale