from .carrello import Carrello


def dati_carrello(request):
    carrello = Carrello(request)

    return {
        "numero_prodotti_carrello": len(carrello),
    }