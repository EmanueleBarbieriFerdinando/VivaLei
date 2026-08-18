from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import NuovaChatForm, RispostaChatForm
from .models import (
    AllegatoMessaggio,
    Chat,
    Messaggio,
    NotificaStaff,
)


@login_required(login_url="users:login")
def crea_chat(request):

    if request.method == "POST":

        form = NuovaChatForm(
            request.POST
        )

        if form.is_valid():

            chat = form.save(
                commit=False
            )

            chat.cliente = request.user
            chat.save()


            messaggio = Messaggio.objects.create(
                chat=chat,
                testo=form.cleaned_data["messaggio"],
                mittente_staff=False,
            )


            for file in request.FILES.getlist("allegati"):

                AllegatoMessaggio.objects.create(
                    messaggio=messaggio,
                    file=file,
                    nome=file.name,
                )


            NotificaStaff.objects.create(
                chat=chat,
                testo=f"Nuova richiesta da {request.user.email}",
            )


            messages.success(
                request,
                "La tua richiesta è stata inviata correttamente.",
            )


            return redirect(
                "support:mie_richieste"
            )


    else:

        form = NuovaChatForm()


    return render(
        request,
        "support/crea_chat.html",
        {
            "form": form,
        }
    )



@login_required(login_url="users:login")
def mie_richieste(request):

    chats = (
        Chat.objects
        .filter(
            cliente=request.user
        )
        .order_by(
            "-data_modifica"
        )
    )


    return render(
        request,
        "support/mie_richieste.html",
        {
            "chats": chats,
        }
    )



@login_required(login_url="users:login")
def dettaglio_chat(request, chat_id):

    chat = get_object_or_404(
        Chat.objects.prefetch_related(
            "messaggi__allegati"
        ),
        id=chat_id,
        cliente=request.user,
    )


    Messaggio.objects.filter(
        chat=chat,
        mittente_staff=True,
        letto=False,
    ).update(
        letto=True
    )


    if request.method == "POST":


        if chat.stato == Chat.Stato.CHIUSA:

            messages.error(
                request,
                "Questa richiesta è già stata chiusa.",
            )

            return redirect(
                "support:dettaglio_chat",
                chat_id=chat.id,
            )



        form = RispostaChatForm(
            request.POST
        )


        if form.is_valid():

            messaggio = form.save(
                commit=False
            )


            messaggio.chat = chat
            messaggio.mittente_staff = False
            messaggio.save()



            for file in request.FILES.getlist("allegati"):

                AllegatoMessaggio.objects.create(
                    messaggio=messaggio,
                    file=file,
                    nome=file.name,
                )



            chat.stato = Chat.Stato.IN_ELABORAZIONE
            chat.cliente_ha_risposto = True
            chat.save()



            NotificaStaff.objects.create(
                chat=chat,
                testo=f"Nuova risposta cliente nella chat {chat.codice}",
            )



            return redirect(
                "support:dettaglio_chat",
                chat_id=chat.id,
            )


    else:

        form = RispostaChatForm()



    return render(
        request,
        "support/dettaglio_chat.html",
        {
            "chat": chat,
            "form": form,
        }
    )



@login_required(login_url="users:login")
def chiudi_chat(request, chat_id):

    chat = get_object_or_404(
        Chat,
        id=chat_id,
        cliente=request.user,
    )


    chat.stato = Chat.Stato.CHIUSA
    chat.data_chiusura = timezone.now()
    chat.chiusa_da_cliente = True

    chat.save()



    messages.success(
        request,
        "La richiesta è stata chiusa.",
    )


    return redirect(
        "support:mie_richieste"
    )