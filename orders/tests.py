from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import NotificaOrdine, Ordine, RigaOrdine, RigaSessioneCheckout, SessioneCheckout
from .services import invia_email_ordine_ricevuto


class ConfermaPagamentoStripeTests(TestCase):
    def setUp(self):
        self.utente = get_user_model().objects.create_user(
            email="cliente@example.com",
            password="password-test",
        )
        self.sessione = SessioneCheckout.objects.create(
            utente=self.utente,
            nome="Mario",
            cognome="Rossi",
            email="cliente@example.com",
            indirizzo="Via Roma",
            numero_civico="1",
            cap="00100",
            citta="Roma",
            provincia="RM",
            totale=Decimal("14.90"),
            subtotale=Decimal("14.90"),
            stripe_checkout_session_id="cs_test_pagata",
        )
        RigaSessioneCheckout.objects.create(
            sessione=self.sessione,
            nome_prodotto="Prodotto test",
            sku="TEST-0001",
            prezzo_unitario=Decimal("14.90"),
            quantita=1,
        )
        self.sessione_stripe = SimpleNamespace(
            id="cs_test_pagata",
            status="complete",
            payment_status="paid",
            amount_total=1490,
            currency="eur",
            payment_intent="pi_test_pagato",
        )

    @patch("orders.views.stripe.checkout.Session.retrieve")
    def test_ritorno_da_stripe_crea_ordine_e_mostra_conferma(self, retrieve):
        retrieve.return_value = self.sessione_stripe
        self.client.force_login(self.utente)

        risposta = self.client.get(
            reverse("orders:riepilogo_checkout", kwargs={"token": self.sessione.token}),
            {"checkout": "success"},
            follow=True,
        )

        self.sessione.refresh_from_db()
        self.assertEqual(risposta.status_code, 200)
        self.assertEqual(self.sessione.stato, SessioneCheckout.Stato.COMPLETATA)
        self.assertIsNotNone(self.sessione.ordine_id)
        self.assertEqual(self.sessione.ordine.stato_pagamento, Ordine.StatoPagamento.PAGATO)
        self.assertTrue(self.sessione.ordine.notifiche.filter(tipo=NotificaOrdine.Tipo.ORDINE_RICEVUTO).exists())
        self.assertContains(risposta, "Grazie per il tuo ordine")
        self.assertContains(risposta, "Ordine")

    @patch("orders.views.stripe.checkout.Session.retrieve")
    def test_ritorno_non_pagato_non_crea_ordine(self, retrieve):
        retrieve.return_value = SimpleNamespace(
            id="cs_test_pagata",
            status="open",
            payment_status="unpaid",
        )
        self.client.force_login(self.utente)

        risposta = self.client.get(
            reverse("orders:riepilogo_checkout", kwargs={"token": self.sessione.token}),
            {"checkout": "success"},
        )

        self.sessione.refresh_from_db()
        self.assertEqual(risposta.status_code, 200)
        self.assertIsNone(self.sessione.ordine_id)
        self.assertContains(risposta, "Stiamo verificando il pagamento con Stripe")


class EmailOrdineTests(TestCase):
    def test_la_mail_di_conferma_contiene_i_dati_dell_ordine(self):
        utente = get_user_model().objects.create_user(email="cliente@example.com", password="password-test")
        ordine = Ordine.objects.create(
            utente=utente,
            stato=Ordine.Stato.PAGATO,
            stato_pagamento=Ordine.StatoPagamento.PAGATO,
            nome="Mario",
            cognome="Rossi",
            email=utente.email,
            telefono="3331234567",
            indirizzo="Via Roma",
            numero_civico="1",
            cap="00100",
            citta="Roma",
            provincia="RM",
            note="Citofonare Rossi",
            subtotale=Decimal("14.90"),
            totale=Decimal("14.90"),
        )
        RigaOrdine.objects.create(
            ordine=ordine,
            nome_prodotto="Prodotto test",
            sku="TEST-0001",
            prezzo_unitario=Decimal("14.90"),
            quantita=1,
        )
        notifica = NotificaOrdine.objects.create(
            ordine=ordine,
            tipo=NotificaOrdine.Tipo.ORDINE_RICEVUTO,
            destinatario=utente.email,
        )

        with patch("orders.services.invia_email") as invia_email_mock:
            self.assertTrue(invia_email_ordine_ricevuto(notifica.pk))

        notifica.refresh_from_db()
        self.assertEqual(notifica.stato, NotificaOrdine.Stato.INVIATA)
        self.assertEqual(invia_email_mock.call_args.kwargs["destinatari"], [utente.email])
        self.assertIn("Prodotto test", invia_email_mock.call_args.kwargs["corpo_html"])
        self.assertIn("Via Roma 1", invia_email_mock.call_args.kwargs["corpo_html"])


class GestioneOrdineTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            email="staff@example.com",
            password="password-test",
            is_staff=True,
        )
        self.cliente = get_user_model().objects.create_user(
            email="cliente-logistica@example.com",
            password="password-test",
        )
        self.ordine = Ordine.objects.create(
            utente=self.cliente,
            stato=Ordine.Stato.PAGATO,
            stato_pagamento=Ordine.StatoPagamento.PAGATO,
            nome="Mario",
            cognome="Rossi",
            email=self.cliente.email,
            indirizzo="Via Roma",
            numero_civico="1",
            cap="00100",
            citta="Roma",
            provincia="RM",
            totale=Decimal("14.90"),
            subtotale=Decimal("14.90"),
        )
        self.client.force_login(self.staff)

    def test_salvataggio_tracking_spedisce_ordine(self):
        risposta = self.client.post(
            reverse("orders:dettaglio", kwargs={"codice": self.ordine.codice}),
            {
                "corriere": "BRT",
                "codice_tracking": "TRACK-123",
                "url_tracking": "https://example.com/tracking/TRACK-123",
            },
        )

        self.ordine.refresh_from_db()
        self.assertRedirects(risposta, reverse("orders:dettaglio", kwargs={"codice": self.ordine.codice}))
        self.assertEqual(self.ordine.stato, Ordine.Stato.SPEDITO)
        self.assertEqual(self.ordine.corriere, "BRT")
        self.assertEqual(self.ordine.codice_tracking, "TRACK-123")
        self.assertIsNotNone(self.ordine.data_spedizione)

    def test_note_interne_non_modificano_la_spedizione(self):
        self.ordine.corriere = "GLS"
        self.ordine.codice_tracking = "TRACK-ESISTENTE"
        self.ordine.save()

        risposta = self.client.post(
            reverse("orders:dettaglio", kwargs={"codice": self.ordine.codice}),
            {"azione": "salva_note", "nota_interna": "Consegnare al magazzino entro venerdì."},
        )

        self.ordine.refresh_from_db()
        self.assertRedirects(risposta, reverse("orders:dettaglio", kwargs={"codice": self.ordine.codice}))
        self.assertEqual(self.ordine.nota_interna, "Consegnare al magazzino entro venerdì.")
        self.assertEqual(self.ordine.corriere, "GLS")
        self.assertEqual(self.ordine.codice_tracking, "TRACK-ESISTENTE")

    def test_ordine_arrivato_chiude_un_ordine_spedito(self):
        self.ordine.stato = Ordine.Stato.SPEDITO
        self.ordine.save()

        risposta = self.client.post(
            reverse("orders:dettaglio", kwargs={"codice": self.ordine.codice}),
            {"azione": "ordine_arrivato"},
        )

        self.ordine.refresh_from_db()
        self.assertRedirects(risposta, reverse("orders:dettaglio", kwargs={"codice": self.ordine.codice}))
        self.assertEqual(self.ordine.stato, Ordine.Stato.COMPLETATO)
        self.assertIsNotNone(self.ordine.data_consegna)
