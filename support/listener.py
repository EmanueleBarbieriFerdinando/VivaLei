import os
import sys
import time


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(
    BASE_DIR
)


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)


import django

django.setup()



from support.email_receiver import leggi_email_nonlette
from support.models import (
    Chat,
    Messaggio,
    NotificaStaff,
)





def salva_email_in_chat(email_data):

    codice_chat = email_data.get(
        "codice_chat"
    )


    if not codice_chat:

        print(
            "Email senza codice chat, ignorata"
        )

        return



    try:

        chat = Chat.objects.get(
            codice=codice_chat
        )


    except Chat.DoesNotExist:

        print(
            f"Nessuna chat trovata per {codice_chat}"
        )

        return




    testo = email_data.get(
        "testo",
        ""
    )


    if not testo.strip():

        return




    Messaggio.objects.create(
        chat=chat,
        mittente_staff=False,
        testo=testo,
    )



    chat.cliente_ha_risposto = True

    chat.stato = Chat.Stato.IN_ELABORAZIONE

    chat.save()



    NotificaStaff.objects.create(
        chat=chat,
        testo=f"Nuova risposta cliente nella chat {chat.codice}"
    )



    print(
        f"Nuovo messaggio importato nella chat {chat.codice}"
    )







def avvia_listener():

    print(
        "Listener email VivaLei avviato..."
    )


    while True:


        try:

            email_ricevute = leggi_email_nonlette()



            if email_ricevute:

                print(
                    f"Trovate {len(email_ricevute)} nuove email"
                )



            for email_data in email_ricevute:

                salva_email_in_chat(
                    email_data
                )



        except Exception as errore:

            print(
                "Errore listener:",
                errore
            )



        time.sleep(
            30
        )







if __name__ == "__main__":

    avvia_listener()
    