import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models

from products.models import Prodotto


class Ordine(models.Model):
    class Stato(models.TextChoices):
        IN_ATTESA_PAGAMENTO = "in_attesa_pagamento", "In attesa di pagamento"
        PAGATO = "pagato", "Pagato"
        IN_PREPARAZIONE = "in_preparazione", "In preparazione"
        SPEDITO = "spedito", "Spedito"
        COMPLETATO = "completato", "Consegnato"
        ANNULLATO = "annullato", "Annullato"
        RIMBORSATO = "rimborsato", "Rimborsato"

    class StatoPagamento(models.TextChoices):
        NON_PAGATO = "non_pagato", "Non pagato"
        PAGATO = "pagato", "Pagato"
        FALLITO = "fallito", "Fallito"
        RIMBORSATO = "rimborsato", "Rimborsato"

    codice = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    utente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ordini",
    )

    stato = models.CharField(
        max_length=30,
        choices=Stato.choices,
        default=Stato.IN_ATTESA_PAGAMENTO,
    )

    stato_pagamento = models.CharField(
        max_length=20,
        choices=StatoPagamento.choices,
        default=StatoPagamento.NON_PAGATO,
    )

    # =========================
    # DATI CLIENTE
    # =========================

    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)

    # =========================
    # INDIRIZZO SPEDIZIONE
    # =========================

    indirizzo = models.CharField(max_length=255)
    numero_civico = models.CharField(max_length=20)
    cap = models.CharField(max_length=10)
    citta = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    paese = models.CharField(max_length=100, default="Italia")

    # =========================
    # NOTE
    # =========================

    # Nota inserita dal cliente al checkout
    note = models.TextField(blank=True)

    # Nota privata visibile solo allo staff
    nota_interna = models.TextField(blank=True)

    # =========================
    # SPEDIZIONE
    # =========================

    corriere = models.CharField(
        max_length=100,
        blank=True,
    )

    codice_tracking = models.CharField(
        max_length=255,
        blank=True,
    )

    url_tracking = models.URLField(
        max_length=500,
        blank=True,
    )

    data_spedizione = models.DateTimeField(
        blank=True,
        null=True,
    )

    data_consegna = models.DateTimeField(
        blank=True,
        null=True,
    )

    # =========================
    # TOTALI
    # =========================

    subtotale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    costo_spedizione = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    totale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    valuta = models.CharField(
        max_length=3,
        default="EUR",
    )

    # =========================
    # STRIPE
    # =========================

    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )

    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
    )

    # =========================
    # DATE
    # =========================

    data_creazione = models.DateTimeField(
        auto_now_add=True,
    )

    data_modifica = models.DateTimeField(
        auto_now=True,
    )

    data_pagamento = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-data_creazione"]
        verbose_name = "Ordine"
        verbose_name_plural = "Ordini"

    def __str__(self):
        return f"Ordine {self.codice} - {self.email}"

    @property
    def nome_cliente(self):
        return f"{self.nome} {self.cognome}".strip()

    @property
    def indirizzo_completo(self):
        return f"{self.indirizzo} {self.numero_civico}, {self.cap} {self.citta} ({self.provincia}), {self.paese}"

    @property
    def richiede_azione(self):
        return self.stato not in {
            self.Stato.COMPLETATO,
            self.Stato.ANNULLATO,
            self.Stato.RIMBORSATO,
        }

    @property
    def percentuale_avanzamento(self):
        avanzamento = {
            self.Stato.IN_ATTESA_PAGAMENTO: 10,
            self.Stato.PAGATO: 30,
            self.Stato.IN_PREPARAZIONE: 55,
            self.Stato.SPEDITO: 80,
            self.Stato.COMPLETATO: 100,
        }

        return avanzamento.get(self.stato, 0)


class RigaOrdine(models.Model):
    ordine = models.ForeignKey(
        Ordine,
        on_delete=models.CASCADE,
        related_name="righe",
    )

    prodotto = models.ForeignKey(
        Prodotto,
        on_delete=models.SET_NULL,
        related_name="righe_ordine",
        blank=True,
        null=True,
    )

    # Snapshot del prodotto al momento dell'acquisto
    nome_prodotto = models.CharField(
        max_length=255,
    )

    sku = models.CharField(
        max_length=50,
    )

    prezzo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    quantita = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Riga ordine"
        verbose_name_plural = "Righe ordine"

    @property
    def totale(self):
        return self.prezzo_unitario * self.quantita

    def __str__(self):
        return f"{self.quantita} × {self.nome_prodotto}"


class NotificaOrdine(models.Model):
    class Tipo(models.TextChoices):
        ORDINE_RICEVUTO = "ordine_ricevuto", "Ordine ricevuto"
        PAGAMENTO_CONFERMATO = "pagamento_confermato", "Pagamento confermato"
        SPEDIZIONE = "spedizione", "Ordine spedito"
        ANNULLAMENTO = "annullamento", "Ordine annullato"

    class Stato(models.TextChoices):
        DA_INVIARE = "da_inviare", "Da inviare"
        INVIATA = "inviata", "Inviata"
        ERRORE = "errore", "Errore"

    ordine = models.ForeignKey(
        Ordine,
        on_delete=models.CASCADE,
        related_name="notifiche",
    )

    tipo = models.CharField(
        max_length=30,
        choices=Tipo.choices,
    )

    stato = models.CharField(
        max_length=20,
        choices=Stato.choices,
        default=Stato.DA_INVIARE,
    )

    destinatario = models.EmailField()

    data_creazione = models.DateTimeField(
        auto_now_add=True,
    )

    data_invio = models.DateTimeField(
        blank=True,
        null=True,
    )

    errore = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["-data_creazione"]
        verbose_name = "Notifica ordine"
        verbose_name_plural = "Notifiche ordine"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.ordine.codice}"


class SessioneCheckout(models.Model):
    class Stato(models.TextChoices):
        APERTA = "aperta", "Aperta"
        COMPLETATA = "completata", "Completata"
        SCADUTA = "scaduta", "Scaduta"
        ANNULLATA = "annullata", "Annullata"

    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    utente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sessioni_checkout",
    )

    stato = models.CharField(
        max_length=20,
        choices=Stato.choices,
        default=Stato.APERTA,
    )

    ordine = models.OneToOneField(
        Ordine,
        on_delete=models.SET_NULL,
        related_name="sessione_checkout",
        blank=True,
        null=True,
    )

    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)

    indirizzo = models.CharField(max_length=255)
    numero_civico = models.CharField(max_length=20)
    cap = models.CharField(max_length=10)
    citta = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    paese = models.CharField(max_length=100, default="Italia")

    note = models.TextField(blank=True)

    subtotale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    costo_spedizione = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    totale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    valuta = models.CharField(
        max_length=3,
        default="EUR",
    )

    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )

    data_creazione = models.DateTimeField(
        auto_now_add=True,
    )

    data_modifica = models.DateTimeField(
        auto_now=True,
    )

    data_completamento = models.DateTimeField(
        blank=True,
        null=True,
    )

    data_scadenza = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-data_creazione"]
        verbose_name = "Sessione checkout"
        verbose_name_plural = "Sessioni checkout"

    def __str__(self):
        return f"Checkout {self.token} - {self.email}"


class RigaSessioneCheckout(models.Model):
    sessione = models.ForeignKey(
        SessioneCheckout,
        on_delete=models.CASCADE,
        related_name="righe",
    )

    prodotto = models.ForeignKey(
        Prodotto,
        on_delete=models.SET_NULL,
        related_name="righe_sessione_checkout",
        blank=True,
        null=True,
    )

    nome_prodotto = models.CharField(
        max_length=255,
    )

    sku = models.CharField(
        max_length=50,
    )

    prezzo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    quantita = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Riga sessione checkout"
        verbose_name_plural = "Righe sessione checkout"

    @property
    def totale(self):
        return self.prezzo_unitario * self.quantita

    def __str__(self):
        return f"{self.quantita} × {self.nome_prodotto}"