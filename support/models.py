from django.conf import settings
from django.db import models


class Chat(models.Model):

    class Stato(models.TextChoices):
        APERTA = "aperta", "Aperta"
        IN_ELABORAZIONE = "in_elaborazione", "In elaborazione"
        CHIUSA = "chiusa", "Chiusa"


    class Categoria(models.TextChoices):
        INFORMAZIONI = "informazioni", "Informazioni prodotto"
        ORDINE = "ordine", "Problema ordine"
        SPEDIZIONE = "spedizione", "Spedizione"
        PAGAMENTO = "pagamento", "Pagamento"
        RESO = "reso", "Reso o rimborso"
        ALTRO = "altro", "Altro"


    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat"
    )


    ordine = models.ForeignKey(
        "orders.Ordine",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat"
    )


    codice = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )


    categoria = models.CharField(
        max_length=30,
        choices=Categoria.choices,
        default=Categoria.ALTRO
    )


    oggetto = models.CharField(
        max_length=200
    )


    stato = models.CharField(
        max_length=30,
        choices=Stato.choices,
        default=Stato.APERTA
    )


    cliente_ha_risposto = models.BooleanField(
        default=False
    )


    chiusa_da_cliente = models.BooleanField(
        default=False
    )


    data_apertura = models.DateTimeField(
        auto_now_add=True
    )


    data_modifica = models.DateTimeField(
        auto_now=True
    )


    data_chiusura = models.DateTimeField(
        null=True,
        blank=True
    )


    class Meta:
        ordering = [
            "-data_modifica"
        ]

        verbose_name = "Chat cliente"
        verbose_name_plural = "Chat clienti"


    def save(self, *args, **kwargs):
        if not self.codice:
            super().save(*args, **kwargs)
            self.codice = f"VL-{self.data_apertura.year}-{self.id:06d}"
            Chat.objects.filter(id=self.id).update(
                codice=self.codice
            )
        else:
            super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.codice} - {self.cliente.email}"



class Messaggio(models.Model):

    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messaggi"
    )


    mittente_staff = models.BooleanField(
        default=False
    )


    testo = models.TextField()


    letto = models.BooleanField(
        default=False
    )


    data_creazione = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:
        ordering = [
            "data_creazione"
        ]

        verbose_name = "Messaggio chat"
        verbose_name_plural = "Messaggi chat"


    def __str__(self):
        tipo = "Staff" if self.mittente_staff else "Cliente"
        return f"{tipo} - {self.chat.codice}"



class AllegatoMessaggio(models.Model):

    messaggio = models.ForeignKey(
        Messaggio,
        on_delete=models.CASCADE,
        related_name="allegati"
    )


    file = models.FileField(
        upload_to="chat/allegati/"
    )


    nome = models.CharField(
        max_length=255,
        blank=True
    )


    data_caricamento = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:
        verbose_name = "Allegato messaggio"
        verbose_name_plural = "Allegati messaggi"



class NotificaStaff(models.Model):

    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="notifiche"
    )


    testo = models.CharField(
        max_length=255
    )


    letta = models.BooleanField(
        default=False
    )


    data_creazione = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:
        ordering = [
            "-data_creazione"
        ]

        verbose_name = "Notifica staff"
        verbose_name_plural = "Notifiche staff"


    def __str__(self):
        return self.testo