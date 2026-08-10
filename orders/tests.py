from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Ordine, RigaSessioneCheckout, SessioneCheckout


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
        self.assertContains(risposta, "Pagamento completato")
        self.assertContains(risposta, "Il tuo ordine è stato ricevuto correttamente")

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
