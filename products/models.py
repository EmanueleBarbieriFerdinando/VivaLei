from django.core.validators import RegexValidator
from django.db import models, transaction
from django.db.models import F
from django.urls import reverse
from django.utils.text import slugify


class Categoria(models.Model):
    class Mondo(models.TextChoices):
        CASA = "casa", "La mia casa"
        MOVIMENTO = "movimento", "Tenersi in movimento"
        TEMPO_PER_ME = "tempo-per-me", "Tempo per me"

    nome = models.CharField(
        max_length=100,
        unique=True,
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
    )

    mondo = models.CharField(
        max_length=30,
        choices=Mondo.choices,
        blank=True,
        default="",
        verbose_name="Mondo VivaLei",
    )

    prefisso_sku = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z0-9]+$",
                message="Il prefisso può contenere soltanto lettere e numeri.",
            )
        ],
    )

    ultimo_progressivo_sku = models.PositiveIntegerField(
        default=0,
        editable=False,
    )

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorie"
        ordering = ["nome"]

    def save(self, *args, **kwargs):
        if self.prefisso_sku:
            self.prefisso_sku = self.prefisso_sku.strip().upper()

        if not self.slug:
            self.slug = slugify(self.nome)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


class Prodotto(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prodotti",
    )

    nome = models.CharField(
        max_length=200,
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
    )

    sku = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        editable=False,
        verbose_name="Codice SKU",
    )

    descrizione = models.TextField(
        blank=True,
    )

    prezzo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    quantita_disponibile = models.PositiveIntegerField(
        default=0,
    )

    immagine = models.ImageField(
        upload_to="prodotti/",
        blank=True,
        null=True,
        verbose_name="Immagine principale",
    )

    attivo = models.BooleanField(
        default=True,
    )

    data_creazione = models.DateTimeField(
        auto_now_add=True,
    )

    data_modifica = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Prodotto"
        verbose_name_plural = "Prodotti"
        ordering = ["nome"]

    def save(self, *args, **kwargs):
        if not self.slug:
            slug_base = slugify(self.nome)
            slug = slug_base
            numero = 1

            while Prodotto.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{slug_base}-{numero}"
                numero += 1

            self.slug = slug

        if self.sku:
            super().save(*args, **kwargs)
            return

        if not self.categoria_id:
            raise ValueError(
                "La categoria è obbligatoria per generare lo SKU."
            )

        with transaction.atomic():
            Categoria.objects.filter(pk=self.categoria_id).update(
                ultimo_progressivo_sku=F("ultimo_progressivo_sku") + 1
            )

            categoria = Categoria.objects.get(
                pk=self.categoria_id
            )

            if not categoria.prefisso_sku:
                raise ValueError(
                    "La categoria selezionata non ha un prefisso SKU."
                )

            self.sku = (
                f"{categoria.prefisso_sku}-"
                f"{categoria.ultimo_progressivo_sku:04d}"
            )

            super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "products:dettaglio_prodotto",
            kwargs={
                "slug": self.slug,
            },
        )

    def __str__(self):
        return f"{self.nome} - {self.sku}"

    @property
    def disponibile(self):
        return self.attivo and self.quantita_disponibile > 0


class ImmagineProdotto(models.Model):
    prodotto = models.ForeignKey(
        Prodotto,
        on_delete=models.CASCADE,
        related_name="immagini_extra",
    )

    immagine = models.ImageField(
        upload_to="prodotti/galleria/",
    )

    alt_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Testo alternativo",
    )

    ordine = models.PositiveIntegerField(
        default=0,
    )

    principale = models.BooleanField(
        default=False,
    )

    class Meta:
        verbose_name = "Immagine prodotto"
        verbose_name_plural = "Immagini prodotto"
        ordering = ["ordine", "id"]

    def __str__(self):
        return f"Immagine di {self.prodotto.nome}"