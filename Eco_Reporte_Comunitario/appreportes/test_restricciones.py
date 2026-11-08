"""Las restricciones CHECK, DEFAULT y los índices únicos filtrados existen en SQL Server.

Los cambios se hacen con update() o SQL directo para saltarse las validaciones de Python:
así se comprueba que es la base de datos la que rechaza el dato.
"""
import uuid
from datetime import date, timedelta

from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.urls import reverse

from Eco_Reporte_Comunitario.restricciones import restar_anios
from appinstituciones.models import AsignacionReporte, Institucion
from appterritorio.models import Comunidad, Ubicacion
from appusuarios.models import Ciudadano, Usuario

from .models import CategoriaProblema, HistorialEstado, ReporteAmbiental

HACE_UN_MES = date.today() - timedelta(days=30)


class RestriccionesBaseDeDatosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ciudadano = Ciudadano.objects.create_user("c@eco.sv", "c@eco.sv", "clave-segura-1")
        cls.categoria = CategoriaProblema.objects.get(nombre="Quema de desechos")
        cls.ubicacion = Ubicacion.objects.create(
            comunidad=Comunidad.objects.get(nombre="Las Toreras"), referencia="Frente a la escuela"
        )
        cls.reporte = ReporteAmbiental.objects.create(
            usuario=cls.ciudadano, categoria=cls.categoria, ubicacion=cls.ubicacion,
            titulo="Quema de basura", descripcion="Queman basura todas las tardes.",
            fecha_incidente=HACE_UN_MES, nivel_gravedad=ReporteAmbiental.NivelGravedad.MEDIO,
        )

    def assertRechaza(self, modelo, pk, **valores):
        with self.assertRaises(IntegrityError), transaction.atomic():
            modelo.objects.filter(pk=pk).update(**valores)

    def test_descripcion_del_reporte_requiere_letras_y_10_caracteres(self):
        self.assertRechaza(ReporteAmbiental, self.reporte.pk, descripcion="1234567890")
        self.assertRechaza(ReporteAmbiental, self.reporte.pk, descripcion="Basura")
        self.assertRechaza(ReporteAmbiental, self.reporte.pk, titulo="12345")

    def test_valores_fuera_de_la_lista_y_fecha_futura(self):
        self.assertRechaza(ReporteAmbiental, self.reporte.pk, estado="HOLA")
        self.assertRechaza(ReporteAmbiental, self.reporte.pk, nivel_gravedad="URGENTE")
        self.assertRechaza(ReporteAmbiental, self.reporte.pk, fecha_incidente=date.today() + timedelta(days=1))

    def test_fecha_del_incidente_maximo_cinco_anios_antes(self):
        creado = ReporteAmbiental.objects.get(pk=self.reporte.pk).fecha_creacion.date()
        self.assertRechaza(
            ReporteAmbiental, self.reporte.pk, fecha_incidente=restar_anios(creado, 5) - timedelta(days=1)
        )
        # Hace 400 días (antes rechazado) y justo 5 años atrás: SQL Server los acepta.
        for fecha in (date.today() - timedelta(days=400), restar_anios(creado, 5)):
            ReporteAmbiental.objects.filter(pk=self.reporte.pk).update(fecha_incidente=fecha)
            self.assertEqual(ReporteAmbiental.objects.get(pk=self.reporte.pk).fecha_incidente, fecha)

    def test_codigo_de_envio_no_se_repite(self):
        token = uuid.uuid4()
        ReporteAmbiental.objects.filter(pk=self.reporte.pk).update(token_envio=token)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ReporteAmbiental.objects.create(
                usuario=self.ciudadano, categoria=self.categoria, ubicacion=self.ubicacion,
                titulo="Quema de basura", descripcion="Queman basura todas las tardes.",
                fecha_incidente=HACE_UN_MES, nivel_gravedad=ReporteAmbiental.NivelGravedad.MEDIO,
                token_envio=token,
            )

    def test_descripcion_de_categoria_es_texto_libre(self):
        self.assertRechaza(CategoriaProblema, self.categoria.pk, descripcion="Basura")
        self.assertRechaza(CategoriaProblema, self.categoria.pk, descripcion="@@@@ #### $$$$")

    def test_telefono_solo_numeros_y_un_guion(self):
        for invalido in ("7000-00@0", "70-00-0000", "-70000000", "7000 0000", "7000"):
            self.assertRechaza(Usuario, self.ciudadano.pk, telefono=invalido)
        Usuario.objects.filter(pk=self.ciudadano.pk).update(telefono="7000-0000")

    def test_nombre_y_correo_validos(self):
        self.assertRechaza(Usuario, self.ciudadano.pk, first_name="Ana2")
        self.assertRechaza(Usuario, self.ciudadano.pk, email="correo-sin-arroba")
        Usuario.objects.filter(pk=self.ciudadano.pk).update(first_name="María José", last_name="Núñez")

    def test_coordenadas_en_rango_y_completas(self):
        self.assertRechaza(Ubicacion, self.ubicacion.pk, latitud=200, longitud=0)
        self.assertRechaza(Ubicacion, self.ubicacion.pk, latitud=13.9)
        # Coordenadas de Tokio: válidas en el mundo, pero fuera de El Salvador.
        self.assertRechaza(Ubicacion, self.ubicacion.pk, latitud=35.6, longitud=139.7)
        Ubicacion.objects.filter(pk=self.ubicacion.pk).update(latitud=14.1856102, longitud=-89.2255825)

    def test_historial_solo_acepta_transiciones_permitidas(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            HistorialEstado.objects.create(
                reporte=self.reporte, usuario=self.ciudadano,
                estado_anterior=ReporteAmbiental.Estado.PENDIENTE, estado_nuevo=ReporteAmbiental.Estado.RESUELTO,
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            HistorialEstado.objects.create(
                reporte=self.reporte, usuario=self.ciudadano,
                estado_anterior=ReporteAmbiental.Estado.PENDIENTE, estado_nuevo=ReporteAmbiental.Estado.DESCARTADO,
            )

    def test_solo_una_asignacion_activa_por_reporte(self):
        institucion = Institucion.objects.create(nombre="Alcaldía", tipo=Institucion.Tipo.ALCALDIA)
        AsignacionReporte.objects.create(reporte=self.reporte, institucion=institucion, asignado_por=self.ciudadano)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AsignacionReporte.objects.create(
                reporte=self.reporte, institucion=institucion, asignado_por=self.ciudadano
            )

    def test_insert_directo_usa_los_valores_por_defecto(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO appreportes_reporteambiental "
                "(titulo, descripcion, fecha_incidente, nivel_gravedad, usuario_id, categoria_id, ubicacion_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                ["Basura en la calle", "Hay bolsas de basura en la calle.", HACE_UN_MES, "BAJO",
                 self.ciudadano.pk, self.categoria.pk, self.ubicacion.pk],
            )
        reporte = ReporteAmbiental.objects.get(titulo="Basura en la calle")
        self.assertEqual(reporte.estado, ReporteAmbiental.Estado.PENDIENTE)
        self.assertIsNotNone(reporte.fecha_creacion)


class RestriccionesFormularioTests(TestCase):
    def test_registro_rechaza_telefono_y_nombre_invalidos(self):
        respuesta = self.client.post(reverse("appusuarios:registro"), {
            "first_name": "Ana1", "last_name": "López", "email": "ana@correo.com", "telefono": "70*0@000",
            "password1": "clave-segura-123", "password2": "clave-segura-123",
        })
        self.assertContains(respuesta, "Use solo letras y espacios.")
        self.assertContains(respuesta, "Escriba solo números")
        self.assertFalse(Usuario.objects.filter(email="ana@correo.com").exists())

    def test_reporte_rechaza_descripcion_solo_con_numeros(self):
        ciudadano = Ciudadano.objects.create_user("c@eco.sv", "c@eco.sv", "clave-segura-1")
        self.client.force_login(ciudadano)
        respuesta = self.client.post(reverse("appreportes:crear"), {
            "categoria": CategoriaProblema.objects.first().pk,
            "titulo": "Quema de basura",
            "descripcion": "1234567890",
            "fecha_incidente": HACE_UN_MES.isoformat(),
            "nivel_gravedad": "MEDIO",
            "comunidad": Comunidad.objects.first().pk,
            "referencia": "Frente a la escuela",
        })
        self.assertContains(respuesta, "no se aceptan solo números")
        self.assertFalse(ReporteAmbiental.objects.exists())
