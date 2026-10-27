from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from appinstituciones.models import Institucion
from appterritorio.models import Comunidad, Ubicacion
from appusuarios.models import Administrador, Ciudadano, Responsable, Usuario

from .models import CategoriaProblema, ReporteAmbiental, Seguimiento

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
        cls.otro_ciudadano = Ciudadano.objects.create_user("otro", "o@eco.sv", "clave-segura-1")
        cls.responsable = Responsable.objects.create_user("responsable", "r@eco.sv", "clave-segura-1")
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

    def crear_reporte_en_proceso(self):
        reporte = self.crear_reporte()
        reporte.cambiar_estado(Estado.EN_PROCESO, self.responsable)
        return reporte

    def crear_reporte_resuelto(self):
        reporte = self.crear_reporte_en_proceso()
        reporte.registrar_seguimiento(self.responsable, "Limpieza", "Se retiró la basura")
        reporte.marcar_como_resuelto(self.responsable)
        return reporte

    # --- Roles y permisos ---

    def test_proxies_guardan_su_rol(self):
        self.assertEqual(self.ciudadano.rol, Usuario.Rol.CIUDADANO)
        self.assertEqual(self.responsable.rol, Usuario.Rol.RESPONSABLE)
        self.assertEqual(list(Responsable.objects.all()), [self.responsable])

    def test_obtener_permisos_es_polimorfico(self):
        ciudadano = Usuario.objects.get(pk=self.ciudadano.pk)
        responsable = Usuario.objects.get(pk=self.responsable.pk)
        admin = Usuario.objects.get(pk=self.admin.pk)

        self.assertTrue(ciudadano.puede("crear_reporte"))
        self.assertTrue(ciudadano.puede("aportar_informacion"))
        self.assertFalse(ciudadano.puede("cambiar_estado"))
        self.assertFalse(ciudadano.puede("asignar_reporte"))

        self.assertTrue(responsable.puede("asignar_reporte"))
        self.assertTrue(responsable.puede("cambiar_estado"))
        self.assertFalse(responsable.puede("crear_reporte"))
        self.assertFalse(responsable.puede("eliminar_cualquier_reporte"))

        self.assertTrue(admin.puede("eliminar_cualquier_reporte"))
        self.assertTrue(admin.puede("asignar_reporte"))

    def test_solo_puede_existir_un_administrador(self):
        with self.assertRaises(ValidationError):
            Administrador.objects.create_user("admin2", "a2@eco.sv", "clave-segura-1")
        with self.assertRaises(ValueError):
            Usuario.objects.create_superuser("root", "root@eco.sv", "clave-segura-1")
        self.assertEqual(Administrador.objects.count(), 1)

    def test_no_se_puede_convertir_a_otro_usuario_en_administrador(self):
        usuario = Usuario.objects.get(pk=self.ciudadano.pk)
        usuario.rol = Usuario.Rol.ADMINISTRADOR
        with self.assertRaises(ValidationError):
            usuario.save()

    def test_solo_el_administrador_accede_al_panel_de_administracion(self):
        with self.assertRaises(ValidationError):
            Ciudadano.objects.create_user("staff", "s@eco.sv", "clave-segura-1", is_staff=True)

    def test_responsable_no_necesita_institucion(self):
        self.assertIsNone(self.responsable.institucion)
        self.assertEqual(self.responsable.titulo_panel(), "Casos de la comunidad")

    # --- Ciudadano: su propio reporte ---

    def test_ciudadano_edita_y_elimina_su_reporte_solo_mientras_esta_pendiente(self):
        reporte = self.crear_reporte()
        self.assertTrue(reporte.puede_modificar(self.ciudadano))
        self.assertTrue(reporte.puede_eliminar(self.ciudadano))

        reporte.cambiar_estado(Estado.EN_PROCESO, self.responsable)
        self.assertFalse(reporte.puede_modificar(self.ciudadano))
        self.assertFalse(reporte.puede_eliminar(self.ciudadano))

    def test_ciudadano_no_toca_reportes_ajenos(self):
        reporte = self.crear_reporte()
        self.assertFalse(reporte.puede_modificar(self.otro_ciudadano))
        self.assertFalse(reporte.puede_eliminar(self.otro_ciudadano))
        self.assertFalse(reporte.puede_agregar_evidencia(self.otro_ciudadano))
        self.assertFalse(reporte.puede_aportar_informacion(self.otro_ciudadano))
        with self.assertRaises(PermissionDenied):
            reporte.aportar_informacion(self.otro_ciudadano, "Intento ajeno")

    def test_ciudadano_aporta_fotos_e_informacion_mientras_el_caso_esta_abierto(self):
        reporte = self.crear_reporte()
        self.assertTrue(reporte.puede_agregar_evidencia(self.ciudadano))
        self.assertTrue(reporte.puede_aportar_informacion(self.ciudadano))

        reporte.cambiar_estado(Estado.EN_PROCESO, self.responsable)
        self.assertTrue(reporte.puede_agregar_evidencia(self.ciudadano))
        aporte = reporte.aportar_informacion(self.ciudadano, "Ahora también queman la basura.")
        self.assertTrue(aporte.es_aporte_ciudadano)

    def test_ciudadano_no_aporta_cuando_el_caso_esta_cerrado(self):
        reporte = self.crear_reporte_resuelto()
        self.assertFalse(reporte.puede_agregar_evidencia(self.ciudadano))
        self.assertFalse(reporte.puede_aportar_informacion(self.ciudadano))

    def test_responsable_no_aporta_como_ciudadano(self):
        reporte = self.crear_reporte()
        self.assertFalse(reporte.puede_aportar_informacion(self.responsable))

    # --- Responsable: coordina y da seguimiento ---

    def test_responsable_gestiona_cualquier_reporte_sin_asignacion(self):
        reporte = self.crear_reporte()
        self.assertTrue(reporte.puede_gestionar(self.responsable))
        self.assertFalse(reporte.puede_modificar(self.responsable))
        self.assertFalse(reporte.puede_eliminar(self.responsable))

    def test_responsable_asigna_y_reasigna(self):
        reporte = self.crear_reporte()
        otra = Institucion.objects.create(nombre="MARN", tipo=Institucion.Tipo.GOBIERNO)
        reporte.asignar_a(self.institucion, self.responsable)
        reporte.asignar_a(otra, self.responsable)
        self.assertEqual(reporte.asignaciones.filter(activa=True).count(), 1)
        self.assertEqual(reporte.asignacion_activa().institucion, otra)
        self.assertEqual(list(otra.reportes_asignados()), [reporte])

    def test_ciudadano_no_puede_asignar(self):
        reporte = self.crear_reporte()
        self.assertFalse(reporte.puede_asignar(self.ciudadano))
        with self.assertRaises(PermissionDenied):
            reporte.asignar_a(self.institucion, self.ciudadano)

    def test_no_se_asigna_un_caso_cerrado(self):
        reporte = self.crear_reporte_resuelto()
        self.assertFalse(reporte.puede_asignar(self.responsable))
        with self.assertRaises(ValidationError):
            reporte.asignar_a(self.institucion, self.responsable)

    # --- Estados ---

    def test_flujo_completo_genera_historial(self):
        reporte = self.crear_reporte_resuelto()
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, Estado.RESUELTO)
        self.assertEqual(reporte.historial.count(), 2)
        self.assertFalse(reporte.es_critico())

    def test_no_se_puede_saltar_de_pendiente_a_resuelto(self):
        reporte = self.crear_reporte()
        with self.assertRaises(ValidationError):
            reporte.cambiar_estado(Estado.RESUELTO, self.responsable)

    def test_resolver_requiere_seguimiento_del_responsable(self):
        reporte = self.crear_reporte_en_proceso()
        reporte.aportar_informacion(self.ciudadano, "El problema sigue igual.")
        with self.assertRaises(ValidationError):
            reporte.marcar_como_resuelto(self.responsable)

    def test_descartar_exige_motivo(self):
        reporte = self.crear_reporte()
        with self.assertRaises(ValidationError):
            reporte.cambiar_estado(Estado.DESCARTADO, self.responsable, "   ")
        reporte.cambiar_estado(Estado.DESCARTADO, self.responsable, "Duplicado del reporte #1")
        self.assertEqual(reporte.motivo_descarte(), "Duplicado del reporte #1")
        self.assertFalse(reporte.esta_activo())

    def test_reporte_descartado_se_puede_reabrir(self):
        reporte = self.crear_reporte()
        reporte.cambiar_estado(Estado.DESCARTADO, self.responsable, "No se encontró el problema")
        self.assertEqual(reporte.estados_siguientes(), [Estado.PENDIENTE])
        reporte.cambiar_estado(Estado.PENDIENTE, self.responsable)
        self.assertEqual(reporte.motivo_descarte(), "")

    def test_ciudadano_no_puede_cambiar_estado(self):
        reporte = self.crear_reporte()
        with self.assertRaises(PermissionDenied):
            reporte.cambiar_estado(Estado.EN_PROCESO, self.ciudadano)

    def test_estado_no_se_modifica_directamente(self):
        reporte = self.crear_reporte()
        reporte.estado = Estado.RESUELTO
        with self.assertRaises(ValidationError):
            reporte.save()

    def test_seguimiento_del_responsable_no_es_aporte(self):
        reporte = self.crear_reporte()
        seguimiento = reporte.registrar_seguimiento(self.responsable, "Inspección", "Se visitó el lugar")
        self.assertEqual(seguimiento.tipo, Seguimiento.Tipo.SEGUIMIENTO)
        self.assertFalse(seguimiento.es_aporte_ciudadano)

    # --- Consultas ---

    def test_inicio_es_publico_y_oculta_datos_personales(self):
        self.crear_reporte()
        respuesta = self.client.get("/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Basura en la quebrada")
        self.assertContains(respuesta, "Las Toreras")
        self.assertNotContains(respuesta, self.ciudadano.email)
        self.assertNotContains(respuesta, self.ciudadano.username)

    def test_filtrar_reportes_y_criticos(self):
        alto = self.crear_reporte()
        self.crear_reporte(nivel_gravedad=ReporteAmbiental.NivelGravedad.BAJO)
        descartado = self.crear_reporte()
        descartado.cambiar_estado(Estado.DESCARTADO, self.responsable, "Duplicado")

        self.assertEqual(ReporteAmbiental.objects.filtrar(nivel_gravedad="ALTO").count(), 2)
        self.assertEqual(list(ReporteAmbiental.objects.criticos()), [alto])
        self.assertEqual(ReporteAmbiental.objects.filtrar(comunidad=self.ubicacion.comunidad).count(), 3)


class SuperusuarioTests(TestCase):
    def test_el_superusuario_es_el_administrador(self):
        superusuario = Usuario.objects.create_superuser("root", "root@eco.sv", "clave-segura-1")
        self.assertEqual(superusuario.rol, Usuario.Rol.ADMINISTRADOR)
        self.assertTrue(superusuario.is_staff)
