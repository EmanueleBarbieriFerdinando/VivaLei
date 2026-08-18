import mimetypes
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def invia_email(destinatari, oggetto, corpo_testo, corpo_html=None, allegati=None, reply_to=None, bcc=None):
    if isinstance(destinatari, str):
        destinatari = [destinatari]

    if not destinatari:
        raise ValueError("Devi indicare almeno un destinatario.")

    email = EmailMultiAlternatives(
        subject=oggetto,
        body=corpo_testo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=destinatari,
        reply_to=reply_to or [settings.EMAIL_REPLY_TO],
        bcc=bcc or [],
    )

    if corpo_html:
        email.attach_alternative(corpo_html, "text/html")

    for allegato in allegati or []:
        aggiungi_allegato(email, allegato)

    return email.send(fail_silently=False)


def aggiungi_allegato(email, allegato):
    if isinstance(allegato, (str, Path)):
        email.attach_file(allegato)
        return

    nome_file = allegato.name
    contenuto = allegato.read()
    tipo_mime = mimetypes.guess_type(nome_file)[0] or "application/octet-stream"

    email.attach(nome_file, contenuto, tipo_mime)