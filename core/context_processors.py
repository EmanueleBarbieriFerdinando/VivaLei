from products.models import Prodotto

def search_products(request):
    prodotti_ricerca = Prodotto.objects.filter(attivo=True).select_related("categoria").order_by("-data_creazione")[:6]

    return {
        "prodotti_ricerca": prodotti_ricerca,
    }