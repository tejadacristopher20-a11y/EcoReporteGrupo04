from django.test import TestCase
from django.urls import reverse

from .models import Ciudadano, Usuario


class CuentaTests(TestCase):
    def test_registro_crea_ciudadano_e_inicia_sesion(self):
        respuesta = self.client.post(reverse("appusuarios:registro"), {
            "first_name": "Ana",
            "last_name": "López",
            "email": "Ana@Correo.com",
            "telefono": "70000000",
            "password1": "clave-segura-123",
            "password2": "clave-segura-123",
        })
        self.assertRedirects(respuesta, reverse("appreportes:panel"))
        usuario = Usuario.objects.get(email="ana@correo.com")
        self.assertEqual(usuario.rol, Usuario.Rol.CIUDADANO)
        self.assertEqual(usuario.username, "ana@correo.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)

    def test_registro_rechaza_correo_repetido(self):
        Ciudadano.objects.create_user("ana@correo.com", "ana@correo.com", "clave-segura-123")
        respuesta = self.client.post(reverse("appusuarios:registro"), {
            "first_name": "Ana", "last_name": "López", "email": "ANA@correo.com",
            "password1": "clave-segura-123", "password2": "clave-segura-123",
        })
        self.assertContains(respuesta, "Ya existe una cuenta con este correo")

    def test_ingresar_con_correo(self):
        Ciudadano.objects.create_user("ana@correo.com", "ana@correo.com", "clave-segura-123")
        respuesta = self.client.post(reverse("appusuarios:ingresar"), {
            "username": "ANA@correo.com", "password": "clave-segura-123",
        })
        self.assertRedirects(respuesta, reverse("appreportes:panel"))

    def test_ingresar_con_clave_incorrecta(self):
        Ciudadano.objects.create_user("ana@correo.com", "ana@correo.com", "clave-segura-123")
        respuesta = self.client.post(reverse("appusuarios:ingresar"), {
            "username": "ana@correo.com", "password": "otra",
        })
        self.assertContains(respuesta, "Correo o contraseña incorrectos.")

    def test_superusuario_ingresa_con_su_nombre_de_usuario(self):
        Usuario.objects.create_superuser("admin", "admin@eco.sv", "clave-segura-123")
        self.assertTrue(self.client.login(username="admin", password="clave-segura-123"))

    def test_perfil_requiere_sesion(self):
        respuesta = self.client.get(reverse("appusuarios:perfil"))
        self.assertRedirects(respuesta, f"{reverse('appusuarios:ingresar')}?next={reverse('appusuarios:perfil')}")
