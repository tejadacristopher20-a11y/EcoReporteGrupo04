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
        # Otra persona intenta registrarse con un correo que ya tiene cuenta (con otra contraseña).
        Ciudadano.objects.create_user("ana@correo.com", "ana@correo.com", "clave-segura-123")
        respuesta = self.client.post(reverse("appusuarios:registro"), {
            "first_name": "Ana", "last_name": "López", "email": "ANA@correo.com",
            "password1": "otra-clave-456", "password2": "otra-clave-456",
        })
        self.assertContains(respuesta, "Ya existe una cuenta con este correo")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_doble_clic_en_registrarse_inicia_sesion_sin_error(self):
        datos = {
            "first_name": "Ana", "last_name": "López", "email": "ana@correo.com", "telefono": "70000000",
            "password1": "clave-segura-123", "password2": "clave-segura-123",
        }
        self.client.post(reverse("appusuarios:registro"), datos)
        # El segundo clic llega sin la sesión del primero, como pasa en el navegador.
        segundo = self.client_class()
        respuesta = segundo.post(reverse("appusuarios:registro"), datos, follow=True)
        self.assertRedirects(respuesta, reverse("appreportes:panel"))
        self.assertContains(respuesta, "Tu cuenta ya se había creado")
        self.assertEqual(Usuario.objects.filter(email="ana@correo.com").count(), 1)

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


class VolverAtrasTests(TestCase):
    """Formularios viejos (volver «Atrás») y direcciones que solo reciben formularios."""

    def setUp(self):
        # Este cliente sí revisa el código de seguridad (CSRF), como el navegador.
        self.client = self.client_class(enforce_csrf_checks=True)

    def test_formulario_vencido_recarga_la_pagina_con_aviso(self):
        url = reverse("appusuarios:ingresar")
        respuesta = self.client.post(url, {"username": "ana@correo.com", "password": "x"}, follow=True)
        self.assertRedirects(respuesta, url)
        self.assertContains(respuesta, "La página había expirado")
        self.assertNotContains(respuesta, "CSRF", status_code=200)

    def test_iniciar_sesion_otra_vez_con_la_pagina_vieja_lleva_al_panel(self):
        Ciudadano.objects.create_user("ana@correo.com", "ana@correo.com", "clave-segura-123")
        self.client.force_login(Usuario.objects.get(email="ana@correo.com"))
        respuesta = self.client.post(
            reverse("appusuarios:ingresar"), {"username": "ana@correo.com", "password": "clave-segura-123"},
            follow=True,
        )
        self.assertRedirects(respuesta, reverse("appreportes:panel"))
        self.assertContains(respuesta, "La página había expirado")

    def test_formulario_vencido_en_el_panel_de_administracion(self):
        url = f"{reverse('admin:login')}?next=/admin/"
        respuesta = self.client.post(url, {"username": "admin", "password": "x"})
        self.assertRedirects(respuesta, url)

    def test_cerrar_sesion_abierto_como_pagina_no_da_error_ni_cierra_la_sesion(self):
        usuario = Ciudadano.objects.create_user("ana@correo.com", "ana@correo.com", "clave-segura-123")
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("appusuarios:salir"))
        self.assertRedirects(respuesta, reverse("appreportes:inicio"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)

    def test_cerrar_sesion_con_el_boton_sigue_funcionando(self):
        usuario = Ciudadano.objects.create_user("ana@correo.com", "ana@correo.com", "clave-segura-123")
        self.client = self.client_class()
        self.client.force_login(usuario)
        respuesta = self.client.post(reverse("appusuarios:salir"))
        self.assertRedirects(respuesta, reverse("appreportes:inicio"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_salir_del_panel_de_administracion(self):
        admin = Usuario.objects.create_superuser("admin", "admin@eco.sv", "clave-segura-123")
        self.client = self.client_class()
        self.client.force_login(admin)
        self.assertRedirects(self.client.get("/admin/logout/"), reverse("admin:index"))
        self.assertIn("_auth_user_id", self.client.session)
        self.client.post("/admin/logout/")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_ingreso_fallido_al_panel_no_pide_reenviar_el_formulario(self):
        self.client = self.client_class()
        respuesta = self.client.post(f"{reverse('admin:login')}?next=/admin/", {"username": "x", "password": "y"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "history.replaceState")
        self.assertNotContains(self.client.get(reverse("admin:login")), "history.replaceState")


class AvisoEliminadoEnElPanelTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser("admin", "admin@eco.sv", "clave-segura-123")
        self.client.force_login(self.admin)

    def test_volver_a_un_usuario_borrado_muestra_su_nombre(self):
        ana = Ciudadano.objects.create_user(
            "ana@correo.com", "ana@correo.com", "clave-segura-123", first_name="Ana", last_name="López"
        )
        borrar = f"/admin/appusuarios/usuario/{ana.pk}/delete/"
        self.client.post(borrar, {"post": "yes"})
        self.assertFalse(Usuario.objects.filter(pk=ana.pk).exists())
        # «Atrás» a la ficha o a la confirmación, o doble clic en «Sí, estoy seguro».
        for url, metodo in ((f"/admin/appusuarios/usuario/{ana.pk}/change/", "get"), (borrar, "post")):
            with self.subTest(url=url):
                respuesta = getattr(self.client, metodo)(url, {"post": "yes"} if metodo == "post" else None, follow=True)
                self.assertRedirects(respuesta, reverse("admin:appusuarios_usuario_changelist"))
                self.assertContains(respuesta, "El usuario «Ana López» fue eliminado.")
                self.assertNotContains(respuesta, "no existe")

    def test_id_que_nunca_existio_mantiene_el_aviso_de_django(self):
        respuesta = self.client.get("/admin/appusuarios/usuario/99999/change/", follow=True)
        self.assertContains(respuesta, "no existe")

    def test_aviso_en_femenino(self):
        from appinstituciones.models import Institucion

        institucion = Institucion.objects.create(nombre="Alcaldía de San Ignacio", tipo=Institucion.Tipo.ALCALDIA)
        self.client.post(f"/admin/appinstituciones/institucion/{institucion.pk}/delete/", {"post": "yes"})
        respuesta = self.client.get(f"/admin/appinstituciones/institucion/{institucion.pk}/change/", follow=True)
        self.assertContains(respuesta, "La institución «Alcaldía de San Ignacio» fue eliminada.")


class ResponsableEnElPanelTests(TestCase):
    """Un responsable por institución: el panel de administración muestra el motivo, sin páginas de error."""

    def setUp(self):
        from appinstituciones.models import Institucion

        self.institucion = Institucion.objects.create(nombre="Alcaldía", tipo=Institucion.Tipo.ALCALDIA)
        self.client.force_login(Usuario.objects.create_superuser("admin", "admin@eco.sv", "clave-segura-123"))

    def datos(self, **cambios):
        datos = {
            "username": "ana", "usable_password": "true", "password1": "clave-segura-123",
            "password2": "clave-segura-123", "email": "ana@correo.com", "first_name": "Ana", "last_name": "López",
            "rol": "RESPONSABLE", "telefono": "", "institucion": self.institucion.pk,
        }
        datos.update(cambios)
        return datos

    def test_crear_responsable_sin_institucion_muestra_el_motivo(self):
        respuesta = self.client.post("/admin/appusuarios/usuario/add/", self.datos(institucion=""))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "El responsable debe pertenecer a una institución.")
        self.assertFalse(Usuario.objects.filter(username="ana").exists())

    def test_segundo_responsable_de_la_misma_institucion_muestra_el_motivo(self):
        self.client.post("/admin/appusuarios/usuario/add/", self.datos())
        self.assertTrue(Usuario.objects.filter(username="ana", institucion=self.institucion).exists())
        respuesta = self.client.post(
            "/admin/appusuarios/usuario/add/", self.datos(username="beto", email="beto@correo.com", first_name="Beto")
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Esta institución ya tiene un responsable.")
        self.assertFalse(Usuario.objects.filter(username="beto").exists())

    def test_borrar_una_institucion_con_responsable_no_da_error(self):
        self.client.post("/admin/appusuarios/usuario/add/", self.datos())
        respuesta = self.client.post(
            f"/admin/appinstituciones/institucion/{self.institucion.pk}/delete/", {"post": "yes"}
        )
        self.assertEqual(respuesta.status_code, 200)  # Django explica qué la protege, en lugar de borrarla.
        self.assertTrue(type(self.institucion).objects.filter(pk=self.institucion.pk).exists())
