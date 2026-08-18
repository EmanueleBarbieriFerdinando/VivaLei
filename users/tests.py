from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="maria@example.com",
            password="PasswordSicura123!",
            first_name="Maria",
            last_name="Rossi",
        )
        self.client.force_login(self.user)

    def test_l_utente_puo_aggiornare_i_propri_dati(self):
        response = self.client.post(reverse("users:modifica_profilo"), {
            "first_name": "Giulia",
            "last_name": "Bianchi",
            "email": "giulia@example.com",
            "telefono": "3331234567",
        })

        self.assertRedirects(response, reverse("users:account"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "giulia@example.com")
        self.assertEqual(self.user.telefono, "3331234567")

    def test_il_cambio_password_mantiene_la_sessione(self):
        response = self.client.post(reverse("users:cambia_password"), {
            "old_password": "PasswordSicura123!",
            "new_password1": "NuovaPasswordSicura123!",
            "new_password2": "NuovaPasswordSicura123!",
        })

        self.assertRedirects(response, reverse("users:account"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NuovaPasswordSicura123!"))
        self.assertTrue(self.client.get(reverse("users:account")).wsgi_request.user.is_authenticated)

# Create your tests here.
