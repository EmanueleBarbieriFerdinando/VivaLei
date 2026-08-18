from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from orders.models import Ordine
from products.models import Categoria, ImmagineProdotto, Prodotto

from support.forms import RispostaChatForm
from support.models import (
    AllegatoMessaggio,
    Chat,
)

from support.services import (
    invia_email_chat,
    crea_testo_email_cliente,
)

from .forms import CategoriaForm, GestioneUtenteForm, ProdottoForm


User = get_user_model()



def salva_immagini_extra(request, prodotto):

    immagini = request.FILES.getlist(
        "immagini_extra"
    )


    if not immagini:
        return


    ultimo_ordine = (
        prodotto.immagini_extra
        .aggregate(
            massimo=Max("ordine")
        )
        .get("massimo")
    )


    ordine = (
        ultimo_ordine or 0
    ) + 1


    for immagine in immagini:

        ImmagineProdotto.objects.create(
            prodotto=prodotto,
            immagine=immagine,
            alt_text=prodotto.nome,
            ordine=ordine,
        )


        ordine += 1




def elimina_immagini_extra(request, prodotto):

    immagini_da_eliminare = request.POST.getlist(
        "elimina_immagini"
    )


    if not immagini_da_eliminare:
        return


    immagini = prodotto.immagini_extra.filter(
        id__in=immagini_da_eliminare
    )


    for immagine in immagini:

        if immagine.immagine:

            immagine.immagine.delete(
                save=False
            )


        immagine.delete()


def sostituisci_immagini_extra(request, prodotto):

    for immagine in prodotto.immagini_extra.all():

        nuova_immagine = request.FILES.get(
            f"sostituisci_immagine_{immagine.id}"
        )

        if not nuova_immagine:
            continue

        if immagine.immagine:
            immagine.immagine.delete(save=False)

        immagine.immagine = nuova_immagine
        immagine.alt_text = prodotto.nome
        immagine.save(update_fields=["immagine", "alt_text"])


@staff_member_required(login_url="users:login")
def dashboard(request):

    context = {

        "numero_utenti": User.objects.count(),

        "utenti_attivi": User.objects.filter(
            is_active=True
        ).count(),

        "utenti_staff": User.objects.filter(
            is_staff=True
        ).count(),

    }


    return render(
        request,
        "gestione/dashboard.html",
        context,
    )





@staff_member_required(login_url="users:login")
def gestione_ordini(request):

    ricerca = request.GET.get(
        "q",
        ""
    ).strip()


    stato = request.GET.get(
        "stato",
        ""
    )


    pagamento = request.GET.get(
        "pagamento",
        ""
    )


    solo_da_gestire = (
        request.GET.get("da_gestire") == "1"
    )



    ordini = (
        Ordine.objects
        .select_related(
            "utente"
        )
        .prefetch_related(
            "righe"
        )
        .order_by(
            "-data_creazione"
        )
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

        ordini = ordini.filter(
            stato=stato
        )



    if pagamento:

        ordini = ordini.filter(
            stato_pagamento=pagamento
        )



    if solo_da_gestire:

        ordini = ordini.exclude(

            stato__in=[

                Ordine.Stato.COMPLETATO,

                Ordine.Stato.ANNULLATO,

                Ordine.Stato.RIMBORSATO,

            ]

        )



    paginator = Paginator(
        ordini,
        15
    )


    pagina = paginator.get_page(
        request.GET.get("page")
    )


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

    ricerca = request.GET.get(
        "q",
        ""
    ).strip()


    stato = request.GET.get(
        "stato",
        ""
    )



    utenti = (
        User.objects
        .all()
        .order_by(
            "-date_joined"
        )
    )



    if ricerca:

        utenti = utenti.filter(

            Q(email__icontains=ricerca)

            | Q(first_name__icontains=ricerca)

            | Q(last_name__icontains=ricerca)

            | Q(telefono__icontains=ricerca)

        )



    if stato == "attivi":

        utenti = utenti.filter(
            is_active=True
        )



    if stato == "disattivati":

        utenti = utenti.filter(
            is_active=False
        )



    if stato == "staff":

        utenti = utenti.filter(
            is_staff=True
        )



    paginator = Paginator(
        utenti,
        10
    )


    pagina = paginator.get_page(
        request.GET.get("page")
    )


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

        return redirect(
            "gestione:utenti"
        )



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


        return redirect(
            "gestione:utenti"
        )



    utente_modificato = form.save(
        commit=False
    )



    if request.user.is_superuser and utente_modificato.is_superuser:

        utente_modificato.is_staff = True



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

    ricerca = request.GET.get(
        "q",
        ""
    ).strip()


    categoria_id = request.GET.get(
        "categoria",
        ""
    )


    stato = request.GET.get(
        "stato",
        ""
    )



    prodotti = (

        Prodotto.objects

        .select_related(
            "categoria"
        )

        .prefetch_related(
            "immagini_extra"
        )

        .order_by(
            "-data_creazione"
        )

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
        10
    )


    pagina = paginator.get_page(
        request.GET.get("page")
    )



    context = {

        "pagina": pagina,

        "form_prodotto": ProdottoForm(),

        "form_categoria": CategoriaForm(),

        "categorie": Categoria.objects.order_by(
            "nome"
        ),

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

        immagine_principale_precedente = prodotto.immagine

        prodotto = form.save()


        if (
            request.POST.get("elimina_immagine_principale")
            and not request.FILES.get("immagine")
            and prodotto.immagine
        ):
            prodotto.immagine.delete(save=False)
            prodotto.immagine = None
            prodotto.save(update_fields=["immagine", "data_modifica"])

        elif (
            request.FILES.get("immagine")
            and immagine_principale_precedente
            and immagine_principale_precedente.name != prodotto.immagine.name
        ):
            immagine_principale_precedente.delete(save=False)


        elimina_immagini_extra(
            request,
            prodotto,
        )


        sostituisci_immagini_extra(
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


@staff_member_required(login_url="users:login")
def elimina_prodotto(request, prodotto_id):

    if request.method != "POST":
        return redirect("gestione:prodotti")

    prodotto = get_object_or_404(Prodotto, id=prodotto_id)
    nome_prodotto = prodotto.nome

    if prodotto.immagine:
        prodotto.immagine.delete(save=False)

    for immagine in prodotto.immagini_extra.all():
        if immagine.immagine:
            immagine.immagine.delete(save=False)

    prodotto.delete()

    messages.success(request, f"Il prodotto {nome_prodotto} è stato eliminato.")

    return redirect("gestione:prodotti")





# ==========================
# GESTIONE CHAT CLIENTI
# ==========================



@staff_member_required(login_url="users:login")
def gestione_chat(request):

    ricerca = request.GET.get(
        "q",
        ""
    ).strip()


    stato = request.GET.get(
        "stato",
        ""
    )


    categoria = request.GET.get(
        "categoria",
        ""
    )


    chats = (

        Chat.objects

        .select_related(
            "cliente",
            "ordine",
        )

        .prefetch_related(
            "messaggi"
        )

        .order_by(
            "-data_modifica"
        )

    )



    if not stato:

        chats = chats.filter(

            stato__in=[

                Chat.Stato.APERTA,

                Chat.Stato.IN_ELABORAZIONE,

            ]

        )


    else:

        chats = chats.filter(
            stato=stato
        )



    if categoria:

        chats = chats.filter(
            categoria=categoria
        )



    if ricerca:

        chats = chats.filter(

            Q(codice__icontains=ricerca)

            | Q(cliente__email__icontains=ricerca)

            | Q(oggetto__icontains=ricerca)

            | Q(messaggi__testo__icontains=ricerca)

        ).distinct()



    paginator = Paginator(
        chats,
        15
    )


    pagina = paginator.get_page(
        request.GET.get("page")
    )


    context = {

        "pagina": pagina,

        "ricerca": ricerca,

        "stato": stato,

        "categoria": categoria,

        "stati_chat": Chat.Stato.choices,

        "categorie_chat": Chat.Categoria.choices,

        "numero_risultati": paginator.count,

    }



    return render(
        request,
        "gestione/gestione_chat.html",
        context,
    )





@staff_member_required(login_url="users:login")
def dettaglio_chat(request, chat_id):

    chat = get_object_or_404(

        Chat.objects

        .select_related(
            "cliente",
            "ordine",
        )

        .prefetch_related(
            "messaggi__allegati"
        ),

        id=chat_id,

    )



    if request.method == "POST":

        form = RispostaChatForm(
            request.POST
        )


        if form.is_valid():

            messaggio = form.save(
                commit=False
            )


            messaggio.chat = chat

            messaggio.mittente_staff = True

            messaggio.save()



            allegati = request.FILES.getlist(
                "allegati"
            )


            for allegato in allegati:

                AllegatoMessaggio.objects.create(

                    messaggio=messaggio,

                    file=allegato,

                    nome=allegato.name,

                )



            chat.stato = Chat.Stato.IN_ELABORAZIONE

            chat.cliente_ha_risposto = False

            chat.save()



            invia_email_chat(

                chat.cliente.email,

                chat.codice,

                crea_testo_email_cliente(

                    chat,

                    messaggio.testo,

                ),

                allegati,

            )



            messages.success(
                request,
                "Risposta inviata correttamente.",
            )


            return redirect(
                "gestione:dettaglio_chat",
                chat_id=chat.id,
            )



    else:

        form = RispostaChatForm()



    return render(

        request,

        "gestione/dettaglio_chat.html",

        {

            "chat": chat,

            "form": form,

        },

    )





@staff_member_required(login_url="users:login")
def chiudi_chat_staff(request, chat_id):

    chat = get_object_or_404(
        Chat,
        id=chat_id,
    )


    chat.stato = Chat.Stato.CHIUSA

    chat.data_chiusura = timezone.now()

    chat.save()



    messages.success(
        request,
        "La chat è stata chiusa.",
    )


    return redirect(
        "gestione:chat"
    )
