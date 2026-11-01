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


class PanelAdministracionTests(TestCase):
    def test_no_hay_borrado_en_bloque_pero_si_desde_la_ficha(self):
        admin = Usuario.objects.create_superuser("admin", "admin@eco.sv", "clave-segura-123")
        self.client.force_login(admin)
        lista = self.client.get("/admin/appusuarios/usuario/")
        self.assertEqual(lista.status_code, 200)
        self.assertNotContains(lista, "delete_selected")
        ficha = self.client.get(f"/admin/appusuarios/usuario/{admin.pk}/delete/")
        self.assertEqual(ficha.status_code, 200)


class RegistroTelefonoYClaveTests(TestCase):
    def datos(self, **cambios):
        datos = {
            "first_name": "Ana", "last_name": "López", "email": "ana@correo.com", "telefono": "7000-0000",
            "password1": "clave-segura-123", "password2": "clave-segura-123",
        }
        datos.update(cambios)
        return datos

    def registrar(self, **cambios):
        return self.client.post(reverse("appusuarios:registro"), self.datos(**cambios))

    def test_telefono_valido_con_y_sin_guion(self):
        for telefono, correo in (("7000-0000", "a@correo.com"), ("70000000", "b@correo.com")):
            with self.subTest(telefono=telefono):
                self.client.logout()
                self.registrar(telefono=telefono, email=correo)
                self.assertTrue(Usuario.objects.filter(email=correo, telefono=telefono).exists())

    def test_telefono_es_obligatorio(self):
        respuesta = self.registrar(telefono="")
        self.assertContains(respuesta, "Escriba su número de teléfono.")
        self.assertFalse(Usuario.objects.exists())

    def test_telefono_invalido(self):
        casos = {
            "700000001": "como máximo 8 números",
            "7000-00001": "como máximo 8 números",
            "7000": "debe tener 8 números",
            "70-00-0000": "un único guion medio",
            "-70000000": "debe ir entre los números",
            "7000 0000": "Escriba solo números",
            "7000-abcd": "Escriba solo números",
        }
        for telefono, mensaje in casos.items():
            with self.subTest(telefono=telefono):
                respuesta = self.registrar(telefono=telefono)
                self.assertContains(respuesta, mensaje)
        self.assertFalse(Usuario.objects.exists())

    def test_clave_requiere_numero_y_simbolo(self):
        respuesta = self.registrar(password1="claveseguraverde", password2="claveseguraverde")
        self.assertContains(respuesta, "La contraseña debe incluir al menos un número")
        self.assertContains(respuesta, "La contraseña debe incluir al menos un símbolo")
        respuesta = self.registrar(password1="claveverde2026", password2="claveverde2026")
        self.assertContains(respuesta, "La contraseña debe incluir al menos un símbolo")
        self.assertFalse(Usuario.objects.exists())

    def test_formulario_muestra_los_requisitos_de_la_clave(self):
        respuesta = self.client.get(reverse("appusuarios:registro"))
        self.assertContains(respuesta, "Su contraseña debe incluir al menos un número")
        self.assertContains(respuesta, "Su contraseña debe incluir al menos un símbolo")
