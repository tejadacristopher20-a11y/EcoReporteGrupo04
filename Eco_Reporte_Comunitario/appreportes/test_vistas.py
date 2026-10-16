import io
import shutil
import tempfile
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from appinstituciones.models import Institucion
from appterritorio.models import Comunidad, Ubicacion
from appusuarios.models import Administrador, Ciudadano, Responsable

from .models import CategoriaProblema, ReporteAmbiental

MEDIA_TEMPORAL = tempfile.mkdtemp()


def imagen_de_prueba(nombre="foto.png"):
    contenido = io.BytesIO()
    Image.new("RGB", (10, 10), "green").save(contenido, "PNG")
    return SimpleUploadedFile(nombre, contenido.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class VistasReportesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        cls.comunidad = Comunidad.objects.get(nombre="Las Toreras")
        cls.categoria = CategoriaProblema.objects.get(nombre="Quema de desechos")
        cls.institucion = Institucion.objects.create(nombre="Alcaldía", tipo=Institucion.Tipo.ALCALDIA)
        cls.ciudadano = Ciudadano.objects.create_user("c@eco.sv", "c@eco.sv", "clave-segura-1", first_name="Carlos")
        cls.otro = Ciudadano.objects.create_user("o@eco.sv", "o@eco.sv", "clave-segura-1")
        cls.responsable = Responsable.objects.create_user(
            "r@eco.sv", "r@eco.sv", "clave-segura-1", institucion=cls.institucion
        )
        cls.admin = Administrador.objects.create_user("a@eco.sv", "a@eco.sv", "clave-segura-1")

    def datos_reporte(self, **cambios):
        datos = {
            "categoria": self.categoria.pk,
            "titulo": "Quema de basura junto a la escuela",
            "descripcion": "Todas las tardes queman basura.",
            "fecha_incidente": "2026-10-01",
            "nivel_gravedad": "ALTO",
            "comunidad": self.comunidad.pk,
            "referencia": "Frente a la escuela",
            "direccion": "",
            "latitud": "14.1234567",
            "longitud": "-89.1234567",
        }
        datos.update(cambios)
        return datos

    def crear_reporte(self, usuario=None):
        ubicacion = Ubicacion.objects.create(comunidad=self.comunidad, referencia="Calle principal")
        return ReporteAmbiental.objects.create(
            usuario=usuario or self.ciudadano, categoria=self.categoria, ubicacion=ubicacion,
            titulo="Basura acumulada", descripcion="Hay basura", fecha_incidente=date(2026, 10, 1),
            nivel_gravedad="MEDIO",
        )

    def test_paginas_publicas(self):
        reporte = self.crear_reporte()
        for url in (reverse("appreportes:inicio"), reverse("appreportes:lista"), reporte.get_absolute_url()):
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 200)
                self.assertNotContains(respuesta, "c@eco.sv")

    def test_crear_reporte_exige_sesion(self):
        respuesta = self.client.get(reverse("appreportes:crear"))
        self.assertRedirects(respuesta, f"{reverse('appusuarios:ingresar')}?next={reverse('appreportes:crear')}")

    def test_ciudadano_crea_reporte_con_foto(self):
        self.client.force_login(self.ciudadano)
        respuesta = self.client.post(reverse("appreportes:crear"), self.datos_reporte(foto=imagen_de_prueba()))
        reporte = ReporteAmbiental.objects.get()
        self.assertRedirects(respuesta, reporte.get_absolute_url())
        self.assertEqual(reporte.usuario, self.ciudadano)
        self.assertEqual(reporte.estado, ReporteAmbiental.Estado.PENDIENTE)
        self.assertEqual(reporte.ubicacion.comunidad, self.comunidad)
        self.assertEqual(reporte.evidencias.count(), 1)

    def test_no_acepta_fecha_futura(self):
        self.client.force_login(self.ciudadano)
        respuesta = self.client.post(reverse("appreportes:crear"), self.datos_reporte(fecha_incidente="2099-01-01"))
        self.assertContains(respuesta, "no puede ser futura")
        self.assertFalse(ReporteAmbiental.objects.exists())

    def test_responsable_no_crea_reportes(self):
        self.client.force_login(self.responsable)
        self.assertEqual(self.client.get(reverse("appreportes:crear")).status_code, 403)

    def test_propietario_edita_y_otro_ciudadano_no(self):
        reporte = self.crear_reporte()
        url = reverse("appreportes:editar", args=[reporte.pk])

        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_login(self.ciudadano)
        respuesta = self.client.post(url, self.datos_reporte(titulo="Título corregido", referencia="Otra referencia"))
        self.assertRedirects(respuesta, reporte.get_absolute_url())
        reporte.refresh_from_db()
        self.assertEqual(reporte.titulo, "Título corregido")
        self.assertEqual(reporte.ubicacion.referencia, "Otra referencia")

    def test_propietario_elimina_su_reporte(self):
        reporte = self.crear_reporte()
        self.client.force_login(self.ciudadano)
        respuesta = self.client.post(reverse("appreportes:eliminar", args=[reporte.pk]))
        self.assertRedirects(respuesta, reverse("appreportes:panel"))
        self.assertFalse(ReporteAmbiental.objects.exists())

    def test_flujo_de_atencion_completo(self):
        reporte = self.crear_reporte()

        # El ciudadano no puede cambiar el estado.
        self.client.force_login(self.ciudadano)
        url_estado = reverse("appreportes:cambiar_estado", args=[reporte.pk])
        self.assertEqual(self.client.post(url_estado, {"estado": "EN_PROCESO"}).status_code, 403)

        # El administrador asigna el caso a la alcaldía.
        self.client.force_login(self.admin)
        self.client.post(reverse("appreportes:asignar", args=[reporte.pk]), {"institucion": self.institucion.pk})

        # El responsable de la alcaldía lo ve en su panel y lo atiende.
        self.client.force_login(self.responsable)
        self.assertContains(self.client.get(reverse("appreportes:panel")), reporte.titulo)
        self.client.post(url_estado, {"estado": "EN_PROCESO"})
        self.client.post(
            reverse("appreportes:registrar_seguimiento", args=[reporte.pk]),
            {"accion": "Limpieza", "descripcion": "Se limpió el lugar."},
        )
        self.client.post(reverse("appreportes:agregar_evidencia", args=[reporte.pk]), {"imagen": imagen_de_prueba()})
        respuesta = self.client.post(url_estado, {"estado": "RESUELTO", "observacion": "Caso cerrado"}, follow=True)

        self.assertContains(respuesta, "El estado del reporte fue actualizado.")
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, ReporteAmbiental.Estado.RESUELTO)
        self.assertEqual(reporte.historial.count(), 2)
        self.assertEqual(reporte.evidencias.count(), 1)

    def test_resolver_sin_seguimiento_muestra_error(self):
        reporte = self.crear_reporte()
        reporte.asignar_a(self.institucion, self.admin)
        reporte.cambiar_estado("EN_PROCESO", self.admin)
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("appreportes:cambiar_estado", args=[reporte.pk]), {"estado": "RESUELTO"}, follow=True
        )
        self.assertContains(respuesta, "Registre al menos un seguimiento")

    def test_panel_de_cada_rol(self):
        self.crear_reporte()
        self.crear_reporte(usuario=self.otro)

        self.client.force_login(self.ciudadano)
        respuesta = self.client.get(reverse("appreportes:panel"))
        self.assertContains(respuesta, "Mis reportes")
        self.assertEqual(respuesta.context["page_obj"].paginator.count, 1)

        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("appreportes:panel"))
        self.assertContains(respuesta, "Todos los reportes")
        self.assertEqual(respuesta.context["page_obj"].paginator.count, 2)

    def test_filtros(self):
        self.crear_reporte()
        respuesta = self.client.get(reverse("appreportes:lista"), {"nivel_gravedad": "ALTO"})
        self.assertEqual(respuesta.context["page_obj"].paginator.count, 0)
        respuesta = self.client.get(reverse("appreportes:lista"), {"buscar": "basura", "estado": "PENDIENTE"})
        self.assertEqual(respuesta.context["page_obj"].paginator.count, 1)
