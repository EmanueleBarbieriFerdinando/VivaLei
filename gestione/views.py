from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404, redirect, render

from orders.models import Ordine
from products.models import Categoria, ImmagineProdotto, Prodotto

from .forms import CategoriaForm, GestioneUtenteForm, ProdottoForm


User = get_user_model()


def salva_immagini_extra(request, prodotto):
    immagini = request.FILES.getlist("immagini_extra")

    if not immagini:
        return

    ultimo_ordine = (
        prodotto.immagini_extra
        .aggregate(massimo=Max("ordine"))
        .get("massimo")
    )

    ordine = (ultimo_ordine or 0) + 1

    for immagine in immagini:
        ImmagineProdotto.objects.create(
            prodotto=prodotto,
            immagine=immagine,
            alt_text=prodotto.nome,
            ordine=ordine,
        )

        ordine += 1


def elimina_immagini_extra(request, prodotto):
    immagini_da_eliminare = request.POST.getlist("elimina_immagini")

    if not immagini_da_eliminare:
        return

    immagini = prodotto.immagini_extra.filter(
        id__in=immagini_da_eliminare
    )

    for immagine in immagini:
        if immagine.immagine:
            immagine.immagine.delete(save=False)

        immagine.delete()


@staff_member_required(login_url="users:login")
def dashboard(request):
    context = {
        "numero_utenti": User.objects.count(),
        "utenti_attivi": User.objects.filter(is_active=True).count(),
        "utenti_staff": User.objects.filter(is_staff=True).count(),
    }

    return render(
        request,
        "gestione/dashboard.html",
        context,
    )


@staff_member_required(login_url="users:login")
def gestione_ordini(request):
    ricerca = request.GET.get("q", "").strip()
    stato = request.GET.get("stato", "")
    pagamento = request.GET.get("pagamento", "")
    solo_da_gestire = request.GET.get("da_gestire") == "1"

    ordini = (
        Ordine.objects
        .select_related("utente")
        .prefetch_related("righe")
        .order_by("-data_creazione")
    )

    if ricerca:
        ordini = ordini.filter(
            Q(email__icontains=ricerca)
            | Q(nome__icontains=ricerca)
            | Q(cognome__icontains=ricerca)
            | Q(codice__icontains=ricerca)
            | Q(codice_tracking__icontains=ricerca)
        )

    if stato:
        ordini = ordini.filter(stato=stato)

    if pagamento:
        ordini = ordini.filter(stato_pagamento=pagamento)

    if solo_da_gestire:
        ordini = ordini.exclude(
            stato__in=[
                Ordine.Stato.COMPLETATO,
                Ordine.Stato.ANNULLATO,
                Ordine.Stato.RIMBORSATO,
            ]
        )

    paginator = Paginator(ordini, 15)
    pagina = paginator.get_page(request.GET.get("page"))

    context = {
        "pagina": pagina,
        "ricerca": ricerca,
        "stato": stato,
        "pagamento": pagamento,
        "solo_da_gestire": solo_da_gestire,
        "stati_ordine": Ordine.Stato.choices,
        "stati_pagamento": Ordine.StatoPagamento.choices,
        "numero_risultati": paginator.count,
    }

    return render(
        request,
        "gestione/gestione_ordini.html",
        context,
    )


@staff_member_required(login_url="users:login")
def gestione_utenti(request):
    ricerca = request.GET.get("q", "").strip()
    stato = request.GET.get("stato", "")

    utenti = User.objects.all().order_by("-date_joined")

    if ricerca:
        utenti = utenti.filter(
            Q(email__icontains=ricerca)
            | Q(first_name__icontains=ricerca)
            | Q(last_name__icontains=ricerca)
            | Q(telefono__icontains=ricerca)
        )

    if stato == "attivi":
        utenti = utenti.filter(is_active=True)

    if stato == "disattivati":
        utenti = utenti.filter(is_active=False)

    if stato == "staff":
        utenti = utenti.filter(is_staff=True)

    paginator = Paginator(utenti, 10)
    pagina = paginator.get_page(request.GET.get("page"))

    context = {
        "pagina": pagina,
        "ricerca": ricerca,
        "stato": stato,
        "numero_risultati": paginator.count,
    }

    return render(
        request,
        "gestione/gestione_utenti.html",
        context,
    )


@staff_member_required(login_url="users:login")
def modifica_utente(request, utente_id):
    utente = get_object_or_404(
        User,
        id=utente_id,
    )

    if request.method != "POST":
        return redirect("gestione:utenti")

    if utente.is_superuser and not request.user.is_superuser:
        messages.error(
            request,
            "Non hai i permessi per modificare un superutente.",
        )

        return redirect("gestione:utenti")

    form = GestioneUtenteForm(
        request.POST,
        instance=utente,
        puo_modificare_ruoli=request.user.is_superuser,
    )

    if not form.is_valid():
        for errori in form.errors.values():
            for errore in errori:
                messages.error(
                    request,
                    errore,
                )

        return redirect("gestione:utenti")

    utente_modificato = form.save(
        commit=False
    )

    if request.user.is_superuser and utente_modificato.is_superuser:
        utente_modificato.is_staff = True

    if utente == request.user and not utente_modificato.is_active:
        messages.error(
            request,
            "Non puoi disattivare il tuo account.",
        )

        return redirect("gestione:utenti")

    if utente == request.user and request.user.is_superuser and not utente_modificato.is_superuser:
        messages.error(
            request,
            "Non puoi rimuovere il ruolo di superutente dal tuo account.",
        )

        return redirect("gestione:utenti")

    if utente == request.user and request.user.is_superuser and not utente_modificato.is_staff:
        messages.error(
            request,
            "Non puoi rimuovere il ruolo staff dal tuo account.",
        )

        return redirect("gestione:utenti")

    utente_modificato.save()

    messages.success(
        request,
        f"L'utente {utente_modificato.email} è stato modificato correttamente.",
    )

    return redirect(
        "gestione:utenti"
    )


@staff_member_required(login_url="users:login")
def gestione_prodotti(request):
    ricerca = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "")
    stato = request.GET.get("stato", "")

    prodotti = (
        Prodotto.objects
        .select_related("categoria")
        .prefetch_related("immagini_extra")
        .order_by("-data_creazione")
    )

    if ricerca:
        prodotti = prodotti.filter(
            Q(nome__icontains=ricerca)
            | Q(sku__icontains=ricerca)
            | Q(descrizione__icontains=ricerca)
        )

    if categoria_id:
        prodotti = prodotti.filter(
            categoria_id=categoria_id
        )

    if stato == "attivi":
        prodotti = prodotti.filter(
            attivo=True
        )

    if stato == "disattivati":
        prodotti = prodotti.filter(
            attivo=False
        )

    if stato == "esauriti":
        prodotti = prodotti.filter(
            quantita_disponibile=0
        )

    paginator = Paginator(
        prodotti,
        10,
    )

    pagina = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "pagina": pagina,
        "form_prodotto": ProdottoForm(),
        "form_categoria": CategoriaForm(),
        "categorie": Categoria.objects.order_by("nome"),
        "ricerca": ricerca,
        "categoria_selezionata": categoria_id,
        "stato": stato,
        "numero_risultati": paginator.count,
    }

    return render(
        request,
        "gestione/gestione_prodotti.html",
        context,
    )


@staff_member_required(login_url="users:login")
def inserisci_prodotto(request):
    if request.method != "POST":
        return redirect(
            "gestione:prodotti"
        )

    form = ProdottoForm(
        request.POST,
        request.FILES,
    )

    if form.is_valid():
        prodotto = form.save()

        salva_immagini_extra(
            request,
            prodotto,
        )

        messages.success(
            request,
            f"Il prodotto {prodotto.nome} è stato inserito correttamente.",
        )

    else:
        for campo, errori in form.errors.items():
            nome_campo = (
                form.fields[campo].label
                if campo in form.fields
                else "Errore"
            )

            for errore in errori:
                messages.error(
                    request,
                    f"{nome_campo}: {errore}",
                )

    return redirect(
        "gestione:prodotti"
    )


@staff_member_required(login_url="users:login")
def inserisci_categoria(request):
    if request.method != "POST":
        return redirect(
            "gestione:prodotti"
        )

    form = CategoriaForm(
        request.POST
    )

    if form.is_valid():
        categoria = form.save()

        messages.success(
            request,
            f"La categoria {categoria.nome} è stata creata correttamente.",
        )

    else:
        for campo, errori in form.errors.items():
            nome_campo = (
                form.fields[campo].label
                if campo in form.fields
                else "Errore"
            )

            for errore in errori:
                messages.error(
                    request,
                    f"{nome_campo}: {errore}",
                )

    return redirect(
        "gestione:prodotti"
    )


@staff_member_required(login_url="users:login")
def modifica_prodotto(request, prodotto_id):
    prodotto = get_object_or_404(
        Prodotto.objects.prefetch_related(
            "immagini_extra"
        ),
        id=prodotto_id,
    )

    if request.method != "POST":
        return redirect(
            "gestione:prodotti"
        )

    form = ProdottoForm(
        request.POST,
        request.FILES,
        instance=prodotto,
    )

    if form.is_valid():
        prodotto = form.save()

        elimina_immagini_extra(
            request,
            prodotto,
        )

        salva_immagini_extra(
            request,
            prodotto,
        )

        messages.success(
            request,
            f"Il prodotto {prodotto.nome} è stato modificato correttamente.",
        )

    else:
        for campo, errori in form.errors.items():
            nome_campo = (
                form.fields[campo].label
                if campo in form.fields
                else "Errore"
            )

            for errore in errori:
                messages.error(
                    request,
                    f"{nome_campo}: {errore}",
                )

    return redirect(
        "gestione:prodotti"
    )