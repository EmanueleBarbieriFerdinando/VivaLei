import email
import imaplib
import re

from email.header import decode_header

from django.conf import settings



def connetti_gmail():

    mail = imaplib.IMAP4_SSL(
        settings.EMAIL_IMAP_HOST,
        settings.EMAIL_IMAP_PORT,
    )


    mail.login(
        settings.EMAIL_IMAP_USER,
        settings.EMAIL_IMAP_PASSWORD,
    )


    return mail





def estrai_testo_email(msg):

    testo = ""


    if msg.is_multipart():

        for parte in msg.walk():

            content_type = parte.get_content_type()

            content_disposition = str(
                parte.get(
                    "Content-Disposition"
                )
            )


            if (
                content_type == "text/plain"
                and "attachment" not in content_disposition
            ):

                try:

                    testo += parte.get_payload(
                        decode=True
                    ).decode(
                        errors="ignore"
                    )

                except Exception:

                    pass


    else:

        try:

            testo = msg.get_payload(
                decode=True
            ).decode(
                errors="ignore"
            )

        except Exception:

            pass



    return testo





def estrai_codice_chat(testo):

    risultato = re.search(
        r"VL-\d{4}-\d{6}",
        testo,
    )


    if risultato:

        return risultato.group(0)


    return None





def decodifica_header(valore):

    if not valore:

        return ""


    risultato = decode_header(
        valore
    )


    testo = ""


    for parte, encoding in risultato:

        if isinstance(
            parte,
            bytes
        ):

            testo += parte.decode(
                encoding or "utf-8",
                errors="ignore",
            )

        else:

            testo += parte



    return testo





def leggi_email_nonlette():

    mail = connetti_gmail()


    mail.select(
        "INBOX"
    )


    stato, dati = mail.search(
        None,
        "UNSEEN",
    )


    email_trovate = []



    if stato != "OK":

        mail.logout()

        return email_trovate





    for numero in dati[0].split():


        stato, contenuto = mail.fetch(
            numero,
            "(RFC822)"
        )


        if stato != "OK":

            continue



        msg = email.message_from_bytes(
            contenuto[0][1]
        )



        mittente = msg.get(
            "From"
        )


        oggetto = decodifica_header(
            msg.get("Subject")
        )


        testo = estrai_testo_email(
            msg
        )


        codice_chat = estrai_codice_chat(
            oggetto + "\n" + testo
        )
        print("OGGETTO:", oggetto)
        print("TESTO:", testo)
        print("CODICE TROVATO:", codice_chat)



        email_trovate.append(
            {
                "mittente": mittente,
                "oggetto": oggetto,
                "testo": testo,
                "codice_chat": codice_chat,
                "numero": numero,
            }
        )



    mail.logout()


    return email_trovate