"""Pruebas de lo que se adaptó para desplegar en Render (PostgreSQL y fotos en la base de datos)."""
import io
import re
from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from Eco_Reporte_Comunitario.restricciones import (
    LETRAS,
    MAXIMO_DIGITOS_SEGUIDOS,
    MAXIMO_LARGO_PALABRA,
    SIGNOS_TEXTO_LIBRE,
    SIMBOLOS_NOMBRE_PERSONA,
    patron_like_a_regex,
)
from appinstituciones.models import Institucion
from appterritorio.models import Comunidad, Ubicacion
from appusuarios.models import Ciudadano, Usuario

from .almacenamiento import AlmacenamientoEnBaseDeDatos
from .models import ArchivoGuardado, CategoriaProblema, ReporteAmbiental


def cumple(patron_like, texto):
    """Lo que haría PostgreSQL con la restricción traducida (operador ~)."""
    return re.search(patron_like_a_regex(patron_like), texto) is not None


class TraduccionLikeAPostgresqlTests(SimpleTestCase):
    """Las restricciones escritas con LIKE de SQL Server deben aceptar y rechazar lo mismo en PostgreSQL."""

    def test_traduccion_basica(self):
        self.assertEqual(patron_like_a_regex("%[A-Z]%"), "^.*[A-Z].*$")
        self.assertEqual(patron_like_a_regex("_____%"), "^" + "." * 5 + ".*$")  # Al menos 5 caracteres.
        self.assertEqual(patron_like_a_regex("%_@_%._%"), r"^.*.@..*\...*$")

    def test_contiene_letras(self):
        patron = f"%[{LETRAS}]%"
        self.assertTrue(cumple(patron, "Basura en la quebrada"))
        self.assertTrue(cumple(patron, "Ñandú 123"))
        self.assertFalse(cumple(patron, "1234567"))
        self.assertFalse(cumple(patron, "!!!"))
        self.assertFalse(cumple(patron, ""))

    def test_nombre_de_persona(self):
        empieza_con_letra = f"[{LETRAS}]%"
        simbolo_no_permitido = f"%[^{LETRAS}{SIMBOLOS_NOMBRE_PERSONA}]%"
        for valido in ("Ana López", "María José", "O'Brien", "Ana-Lucía"):
            with self.subTest(valido=valido):
                self.assertTrue(cumple(empieza_con_letra, valido) and not cumple(simbolo_no_permitido, valido))
        for invalido in ("Ana1", "-Ana", "Ana@", "1Ana"):
            with self.subTest(invalido=invalido):
                self.assertFalse(cumple(empieza_con_letra, invalido) and not cumple(simbolo_no_permitido, invalido))

    def test_texto_libre(self):
        simbolo_raro = f"%[^{LETRAS}0-9\r\n{SIGNOS_TEXTO_LIBRE}]%"
        nueve_digitos = "%" + "[0-9]" * (MAXIMO_DIGITOS_SEGUIDOS + 1) + "%"
        palabra_larga = "%" + "[^ \r\n]" * (MAXIMO_LARGO_PALABRA + 1) + "%"
        bueno = "Hay basura en la calle 5, ¿quién la recoge? (urgente)\nGracias."
        self.assertFalse(cumple(simbolo_raro, bueno))
        self.assertTrue(cumple(simbolo_raro, "Basura <script>"))
        self.assertTrue(cumple(simbolo_raro, "Basura @ calle"))
        self.assertFalse(cumple(nueve_digitos, "Teléfono 7000-0000"))
        self.assertTrue(cumple(nueve_digitos, "Número 123456789"))
        self.assertFalse(cumple(palabra_larga, bueno))
        self.assertTrue(cumple(palabra_larga, "a" * 26))

    def test_telefono(self):
        self.assertTrue(cumple("%[^0-9-]%", "7000 0000"))
        self.assertFalse(cumple("%[^0-9-]%", "7000-0000"))
        self.assertTrue(cumple("%-%-%", "70-00-0000"))
        self.assertTrue(cumple("-%", "-70000000"))
        self.assertTrue(cumple("%-", "70000000-"))

    def test_correo(self):
        self.assertTrue(cumple("%_@_%._%", "ana@correo.com"))
        self.assertFalse(cumple("%_@_%._%", "ana@correo"))
        self.assertTrue(cumple("% %", "ana @correo.com"))


def imagen_de_prueba(nombre="foto.png"):
    contenido = io.BytesIO()
    Image.new("RGB", (12, 12), "green").save(contenido, "PNG")
    return SimpleUploadedFile(nombre, contenido.getvalue(), content_type="image/png")


ALMACENAMIENTO_RENDER = {
    "default": {"BACKEND": "appreportes.almacenamiento.AlmacenamientoEnBaseDeDatos"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(STORAGES=ALMACENAMIENTO_RENDER)
class FotosEnLaBaseDeDatosTests(TestCase):
    """Así funcionan las fotos en Render: guardadas en la base de datos y mostradas en /media/…"""

    @classmethod
    def setUpTestData(cls):
        cls.ciudadano = Ciudadano.objects.create_user("c@eco.sv", "c@eco.sv", "clave-segura-1")
        ubicacion = Ubicacion.objects.create(comunidad=Comunidad.objects.get(nombre="Las Toreras"), referencia="Calle principal")
        cls.reporte = ReporteAmbiental.objects.create(
            usuario=cls.ciudadano, categoria=CategoriaProblema.objects.get(nombre="Quema de desechos"),
            ubicacion=ubicacion, titulo="Basura acumulada", descripcion="Hay basura en la calle",
            fecha_incidente=date.today() - timedelta(days=30), nivel_gravedad="MEDIO",
        )

    def test_almacenamiento_guarda_lee_y_borra(self):
        almacen = AlmacenamientoEnBaseDeDatos()
        nombre = almacen.save("evidencias/2026/11/prueba.webp", io.BytesIO(b"datos de la foto"))
        self.assertEqual(nombre, "evidencias/2026/11/prueba.webp")
        self.assertTrue(almacen.exists(nombre))
        self.assertEqual(almacen.size(nombre), len(b"datos de la foto"))
        with almacen.open(nombre) as archivo:
            self.assertEqual(archivo.read(), b"datos de la foto")
        self.assertEqual(almacen.url(nombre), "/media/evidencias/2026/11/prueba.webp")
        # Un segundo archivo con el mismo nombre no reemplaza al primero.
        otro = almacen.save("evidencias/2026/11/prueba.webp", io.BytesIO(b"otra foto"))
        self.assertNotEqual(otro, nombre)
        almacen.delete(nombre)
        self.assertFalse(almacen.exists(nombre))

    def test_subir_y_ver_una_foto_como_en_render(self):
        self.client.force_login(self.ciudadano)
        self.client.post(reverse("appreportes:agregar_evidencia", args=[self.reporte.pk]), {"imagen": imagen_de_prueba()})
        evidencia = self.reporte.evidencias.get()
        self.assertTrue(ArchivoGuardado.objects.filter(nombre=evidencia.imagen.name).exists())
        url = evidencia.imagen.url
        self.assertTrue(url.startswith("/media/evidencias/") and url.endswith(".webp"))
        # La foto se ve en el detalle y se puede abrir.
        self.assertContains(self.client.get(self.reporte.get_absolute_url()), url)
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "image/webp")
        self.assertEqual(Image.open(io.BytesIO(respuesta.content)).format, "WEBP")
        # Al borrar el reporte, la foto también se borra de la base de datos.
        self.reporte.delete()
        self.assertFalse(ArchivoGuardado.objects.exists())
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_foto_que_no_existe_da_404(self):
        self.assertEqual(self.client.get("/media/evidencias/no-existe.webp").status_code, 404)


class CorreoEnMinusculasTests(TestCase):
    """En PostgreSQL los campos únicos distinguen mayúsculas: el correo siempre se guarda en minúsculas."""

    def test_correo_se_guarda_en_minusculas(self):
        usuario = Ciudadano.objects.create_user("ana@correo.com", "  Ana@Correo.COM ", "clave-segura-123")
        usuario.refresh_from_db()
        self.assertEqual(usuario.email, "ana@correo.com")

    def test_panel_no_permite_el_mismo_correo_con_mayusculas(self):
        institucion = Institucion.objects.create(nombre="Alcaldía", tipo=Institucion.Tipo.ALCALDIA)
        Usuario.objects.create_superuser("admin", "admin@eco.sv", "clave-segura-123")
        self.client.force_login(Usuario.objects.get(username="admin"))
        datos = {
            "username": "ana", "usable_password": "true", "password1": "clave-segura-123",
            "password2": "clave-segura-123", "email": "ana@correo.com", "first_name": "Ana", "last_name": "López",
            "rol": "RESPONSABLE", "telefono": "", "institucion": institucion.pk,
        }
        self.client.post("/admin/appusuarios/usuario/add/", datos)
        otra = Institucion.objects.create(nombre="MARN", tipo=Institucion.Tipo.GOBIERNO)
        datos.update(username="ana2", email="ANA@Correo.com", institucion=otra.pk)
        respuesta = self.client.post("/admin/appusuarios/usuario/add/", datos)
        self.assertEqual(respuesta.status_code, 200)  # Muestra el error en el formulario, sin página de error.
        self.assertEqual(Usuario.objects.filter(email="ana@correo.com").count(), 1)
