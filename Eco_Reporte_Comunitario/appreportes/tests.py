from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from appinstituciones.models import Institucion
from appterritorio.models import Comunidad, Ubicacion
from appusuarios.models import Administrador, Ciudadano, Responsable, Usuario

from .models import CategoriaProblema, ReporteAmbiental

Estado = ReporteAmbiental.Estado


class ReporteAmbientalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Departamento, distrito, comunidad y categorías vienen de las migraciones de datos.
        comunidad = Comunidad.objects.get(nombre="Las Toreras", distrito__nombre="San Ignacio")
        cls.ubicacion = Ubicacion.objects.create(comunidad=comunidad, referencia="Quebrada principal")
        cls.categoria = CategoriaProblema.objects.get(nombre="Botadero clandestino")
        cls.institucion = Institucion.objects.create(nombre="Alcaldía", tipo=Institucion.Tipo.ALCALDIA)

        cls.ciudadano = Ciudadano.objects.create_user("ciudadano", "c@eco.sv", "clave-segura-1")
        cls.responsable = Responsable.objects.create_user(
            "responsable", "r@eco.sv", "clave-segura-1", institucion=cls.institucion
        )
        cls.admin = Administrador.objects.create_user("admin", "a@eco.sv", "clave-segura-1")

    def crear_reporte(self, **datos):
        return ReporteAmbiental.objects.create(
            usuario=self.ciudadano,
            categoria=self.categoria,
            ubicacion=self.ubicacion,
            titulo="Basura en la quebrada",
            descripcion="Acumulación de basura",
            fecha_incidente=date(2026, 10, 1),
            nivel_gravedad=datos.get("nivel_gravedad", ReporteAmbiental.NivelGravedad.ALTO),
        )

    def test_proxies_guardan_su_rol(self):
        self.assertEqual(self.ciudadano.rol, Usuario.Rol.CIUDADANO)
        self.assertEqual(self.responsable.rol, Usuario.Rol.RESPONSABLE)
        self.assertEqual(list(Ciudadano.objects.all()), [self.ciudadano])

    def test_obtener_permisos_es_polimorfico(self):
        usuario = Usuario.objects.get(pk=self.ciudadano.pk)
        self.assertTrue(usuario.puede("crear_reporte"))
        self.assertFalse(usuario.puede("cambiar_estado"))
        self.assertTrue(Usuario.objects.get(pk=self.responsable.pk).puede("cambiar_estado"))
        self.assertTrue(Usuario.objects.get(pk=self.admin.pk).puede("asignar_reporte"))

    def test_superusuario_es_administrador(self):
        superusuario = Usuario.objects.create_superuser("root", "root@eco.sv", "clave-segura-1")
        self.assertEqual(superusuario.rol, Usuario.Rol.ADMINISTRADOR)

    def crear_reporte_asignado(self):
        reporte = self.crear_reporte()
        reporte.asignar_a(self.institucion, self.admin)
        return reporte

    def test_responsable_sin_asignacion_no_gestiona(self):
        reporte = self.crear_reporte()
        self.assertFalse(reporte.puede_gestionar(self.responsable))
        with self.assertRaises(PermissionDenied):
            reporte.cambiar_estado(Estado.EN_PROCESO, self.responsable)
        reporte.asignar_a(self.institucion, self.admin)
        self.assertTrue(reporte.puede_gestionar(self.responsable))

    def test_propietario_solo_edita_mientras_esta_pendiente(self):
        reporte = self.crear_reporte_asignado()
        self.assertTrue(reporte.puede_modificar(self.ciudadano))
        reporte.cambiar_estado(Estado.EN_PROCESO, self.responsable)
        self.assertFalse(reporte.puede_modificar(self.ciudadano))
        self.assertFalse(reporte.puede_eliminar(self.ciudadano))
        self.assertTrue(reporte.puede_modificar(self.admin))

    def test_flujo_completo_genera_historial(self):
        reporte = self.crear_reporte_asignado()
        reporte.cambiar_estado(Estado.EN_PROCESO, self.responsable)
        reporte.registrar_seguimiento(self.responsable, "Limpieza", "Se retiró la basura")
        reporte.marcar_como_resuelto(self.responsable)

        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, Estado.RESUELTO)
        self.assertEqual(reporte.historial.count(), 2)
        self.assertFalse(reporte.es_critico())

    def test_no_se_puede_saltar_de_pendiente_a_resuelto(self):
        reporte = self.crear_reporte_asignado()
        with self.assertRaises(ValidationError):
            reporte.cambiar_estado(Estado.RESUELTO, self.responsable)

    def test_resolver_requiere_seguimiento(self):
        reporte = self.crear_reporte_asignado()
        reporte.cambiar_estado(Estado.EN_PROCESO, self.responsable)
        with self.assertRaises(ValidationError):
            reporte.marcar_como_resuelto(self.responsable)

    def test_ciudadano_no_puede_cambiar_estado(self):
        reporte = self.crear_reporte()
        with self.assertRaises(PermissionDenied):
            reporte.cambiar_estado(Estado.EN_PROCESO, self.ciudadano)

    def test_estado_no_se_modifica_directamente(self):
        reporte = self.crear_reporte()
        reporte.estado = Estado.RESUELTO
        with self.assertRaises(ValidationError):
            reporte.save()

    def test_asignar_desactiva_la_asignacion_anterior(self):
        reporte = self.crear_reporte()
        otra = Institucion.objects.create(nombre="MARN", tipo=Institucion.Tipo.GOBIERNO)
        reporte.asignar_a(self.institucion, self.admin)
        reporte.asignar_a(otra, self.admin)
        self.assertEqual(reporte.asignaciones.filter(activa=True).count(), 1)
        self.assertEqual(reporte.asignacion_activa().institucion, otra)
        self.assertEqual(list(otra.reportes_asignados()), [reporte])

    def test_inicio_es_publico_y_oculta_datos_personales(self):
        self.crear_reporte()
        respuesta = self.client.get("/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Basura en la quebrada")
        self.assertContains(respuesta, "Las Toreras")
        self.assertNotContains(respuesta, self.ciudadano.email)
        self.assertNotContains(respuesta, self.ciudadano.username)

    def test_filtrar_reportes(self):
        alto = self.crear_reporte()
        self.crear_reporte(nivel_gravedad=ReporteAmbiental.NivelGravedad.BAJO)
        self.assertEqual(list(ReporteAmbiental.objects.filtrar(nivel_gravedad="ALTO")), [alto])
        self.assertEqual(list(ReporteAmbiental.objects.criticos()), [alto])
        self.assertEqual(ReporteAmbiental.objects.filtrar(comunidad=self.ubicacion.comunidad).count(), 2)
