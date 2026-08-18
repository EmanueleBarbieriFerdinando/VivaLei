from django.conf import settings
from django.core.mail import EmailMultiAlternatives



def invia_email_chat(
    destinatario,
    codice_chat,
    testo,
    allegati=None,
):

    oggetto = (
        f"VivaLei - Risposta richiesta {codice_chat}"
    )


    email = EmailMultiAlternatives(
        subject=oggetto,
        body=testo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[
            destinatario
        ],
    )


    if allegati:

        for file in allegati:

            email.attach(
                file.name,
                file.read(),
                file.content_type,
            )


    email.send(
        fail_silently=False
    )



def crea_testo_email_cliente(
    chat,
    messaggio,
):

    testo = f"""
Gentile cliente,

abbiamo risposto alla tua richiesta.

Puoi continuare la conversazione rispondendo direttamente a questa email.

Codice richiesta:
{chat.codice}


Messaggio del nostro staff:

{messaggio}


Grazie per aver scelto VivaLei.
"""


    return testo