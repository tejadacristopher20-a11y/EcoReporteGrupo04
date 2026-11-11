import io
import shutil
import tempfile
import uuid
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from Eco_Reporte_Comunitario.restricciones import restar_anios
from appinstituciones.models import Institucion
from appterritorio.models import Comunidad, Ubicacion
from appusuarios.models import Administrador, Ciudadano, Responsable

from .forms import EvidenciaAdminForm
from .models import CategoriaProblema, Evidencia, ReporteAmbiental

MEDIA_TEMPORAL = tempfile.mkdtemp()
HACE_UN_MES = date.today() - timedelta(days=30)


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
        cls.institucion = Institucion.objects.create(
            nombre="Alcaldía", tipo=Institucion.Tipo.ALCALDIA
        )
        cls.ciudadano = Ciudadano.objects.create_user(
            "c@eco.sv", "c@eco.sv", "clave-segura-1", first_name="Carlos"
        )
        cls.otro = Ciudadano.objects.create_user(
            "o@eco.sv", "o@eco.sv", "clave-segura-1"
        )
        cls.responsable = Responsable.objects.create_user(
            "r@eco.sv", "r@eco.sv", "clave-segura-1", institucion=cls.institucion
        )
        cls.admin = Administrador.objects.create_user(
            "a@eco.sv", "a@eco.sv", "clave-segura-1"
        )

    def datos_reporte(self, **cambios):
        datos = {
            "categoria": self.categoria.pk,
            "titulo": "Quema de basura junto a la escuela",
            "descripcion": "Todas las tardes queman basura.",
            "fecha_incidente": HACE_UN_MES.isoformat(),
            "nivel_gravedad": "ALTO",
            "comunidad": self.comunidad.pk,
            "referencia": "Frente a la escuela",
            "direccion": "",
            "latitud": "14.1234567",
            "longitud": "-89.1234567",
        }
        datos.update(cambios)
        return datos

    def crear_reporte(self, usuario=None, asignado=True):
        """Reporte de prueba. Por defecto, asignado a la institución del responsable (lo atiende él)."""
        ubicacion = Ubicacion.objects.create(
            comunidad=self.comunidad, referencia="Calle principal"
        )
        reporte = ReporteAmbiental.objects.create(
            usuario=usuario or self.ciudadano,
            categoria=self.categoria,
            ubicacion=ubicacion,
            titulo="Basura acumulada",
            descripcion="Hay basura en la calle",
            fecha_incidente=HACE_UN_MES,
            nivel_gravedad="MEDIO",
        )
        if asignado:
            reporte.asignar_a(self.institucion, self.admin)
        return reporte

    def test_paginas_publicas(self):
        reporte = self.crear_reporte()
        for url in (
            reverse("appreportes:inicio"),
            reverse("appreportes:lista"),
            reporte.get_absolute_url(),
        ):
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 200)
                self.assertNotContains(respuesta, "c@eco.sv")

    def test_crear_reporte_exige_sesion(self):
        respuesta = self.client.get(reverse("appreportes:crear"))
        self.assertRedirects(
            respuesta,
            f"{reverse('appusuarios:ingresar')}?next={reverse('appreportes:crear')}",
        )

    def test_ciudadano_crea_reporte_con_foto(self):
        self.client.force_login(self.ciudadano)
        respuesta = self.client.post(
            reverse("appreportes:crear"), self.datos_reporte(foto=imagen_de_prueba())
        )
        reporte = ReporteAmbiental.objects.get()
        self.assertRedirects(respuesta, reporte.get_absolute_url())
        self.assertEqual(reporte.usuario, self.ciudadano)
        self.assertEqual(reporte.estado, ReporteAmbiental.Estado.PENDIENTE)
        self.assertEqual(reporte.ubicacion.comunidad, self.comunidad)
        self.assertEqual(reporte.evidencias.count(), 1)

    def test_no_acepta_fecha_futura(self):
        self.client.force_login(self.ciudadano)
        respuesta = self.client.post(
            reverse("appreportes:crear"),
            self.datos_reporte(fecha_incidente="2099-01-01"),
        )
        self.assertContains(respuesta, "no puede ser futura")
        self.assertFalse(ReporteAmbiental.objects.exists())

    def test_no_acepta_fecha_de_hace_mas_de_cinco_anios(self):
        self.client.force_login(self.ciudadano)
        antigua = restar_anios(timezone.now().date(), 5) - timedelta(days=1)
        respuesta = self.client.post(
            reverse("appreportes:crear"),
            self.datos_reporte(fecha_incidente=antigua.isoformat()),
        )
        self.assertContains(respuesta, "hace más de 5 años")
        self.assertFalse(ReporteAmbiental.objects.exists())

    def test_acepta_fechas_de_hasta_cinco_anios_atras(self):
        self.client.force_login(self.ciudadano)
        url = reverse("appreportes:crear")
        # Misma referencia que la app: la fecha de creación del reporte, que se guarda en UTC.
        hoy = timezone.now().date()
        hace_cuatro_anios = restar_anios(hoy, 4)
        limite = restar_anios(hoy, 5)  # Justo 5 años atrás: todavía se acepta.
        for numero, fecha in enumerate((hace_cuatro_anios, limite)):
            with self.subTest(fecha=fecha):
                self.client.post(
                    url,
                    self.datos_reporte(
                        fecha_incidente=fecha.isoformat(),
                        titulo=f"Quema de basura número {numero + 1}",
                    ),
                )
                self.assertTrue(
                    ReporteAmbiental.objects.filter(fecha_incidente=fecha).exists()
                )

    def test_calendario_muestra_el_limite_de_cinco_anios(self):
        self.client.force_login(self.ciudadano)
        respuesta = self.client.get(reverse("appreportes:crear"))
        self.assertContains(
            respuesta, f'min="{restar_anios(timezone.now().date(), 5).isoformat()}"'
        )
        self.assertContains(respuesta, "Puede ser de hasta 5 años atrás.")

    def test_no_acepta_coordenadas_fuera_de_el_salvador(self):
        self.client.force_login(self.ciudadano)
        self.client.post(
            reverse("appreportes:crear"),
            self.datos_reporte(latitud="35.6", longitud="139.7"),
        )
        self.assertFalse(ReporteAmbiental.objects.exists())

    def test_doble_clic_no_crea_reporte_duplicado(self):
        self.client.force_login(self.ciudadano)
        datos = self.datos_reporte(token_envio=str(uuid.uuid4()))
        self.client.post(reverse("appreportes:crear"), datos)
        respuesta = self.client.post(reverse("appreportes:crear"), datos, follow=True)
        reporte = ReporteAmbiental.objects.get()
        self.assertRedirects(respuesta, reporte.get_absolute_url())
        self.assertContains(respuesta, "no se creó un duplicado")

    def test_editar_varias_veces_guarda_el_mismo_reporte(self):
        reporte = self.crear_reporte()
        self.client.force_login(self.ciudadano)
        for titulo in ("Basura acumulada en la calle", "Basura acumulada junto al río"):
            self.client.post(
                reverse("appreportes:editar", args=[reporte.pk]),
                self.datos_reporte(titulo=titulo),
            )
        self.assertEqual(ReporteAmbiental.objects.count(), 1)
        reporte.refresh_from_db()
        self.assertEqual(reporte.titulo, "Basura acumulada junto al río")

    def test_maximo_cinco_fotos_por_reporte(self):
        reporte = self.crear_reporte()
        for numero in range(ReporteAmbiental.MAXIMO_EVIDENCIAS):
            Evidencia.objects.create(
                reporte=reporte, imagen=f"evidencias/foto{numero}.webp"
            )
        self.client.force_login(self.ciudadano)
        respuesta = self.client.post(
            reverse("appreportes:agregar_evidencia", args=[reporte.pk]),
            {"imagen": imagen_de_prueba()},
        )
        self.assertContains(respuesta, "máximo de 5 fotografías")
        self.assertEqual(reporte.evidencias.count(), ReporteAmbiental.MAXIMO_EVIDENCIAS)

    def test_responsable_puede_subir_hasta_diez_fotos(self):
        reporte = self.crear_reporte()
        for numero in range(5):
            Evidencia.objects.create(
                reporte=reporte, imagen=f"evidencias/foto{numero}.webp"
            )
        url = reverse("appreportes:agregar_evidencia", args=[reporte.pk])

        # Con 5 fotos, el ciudadano ya no puede, pero el responsable sí.
        self.client.force_login(self.ciudadano)
        self.client.post(url, {"imagen": imagen_de_prueba()})
        self.assertEqual(reporte.evidencias.count(), 5)
        self.client.force_login(self.responsable)
        self.client.post(url, {"imagen": imagen_de_prueba()})
        self.assertEqual(reporte.evidencias.count(), 6)

        # Al llegar a 10, el responsable también queda topado.
        for numero in range(6, 10):
            Evidencia.objects.create(
                reporte=reporte, imagen=f"evidencias/foto{numero}.webp"
            )
        respuesta = self.client.post(url, {"imagen": imagen_de_prueba()})
        self.assertContains(respuesta, "máximo de 10 fotografías")
        self.assertEqual(reporte.evidencias.count(), 10)

    def test_panel_de_administracion_convierte_fotos_a_webp(self):
        form = EvidenciaAdminForm({"descripcion": ""}, {"imagen": imagen_de_prueba()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data["imagen"].name.endswith(".webp"))

    def test_ficha_del_reporte_en_el_panel_de_administracion(self):
        reporte = self.crear_reporte()
        Administrador.objects.filter(pk=self.admin.pk).update(
            is_staff=True, is_superuser=True
        )
        self.client.force_login(self.admin)
        url = reverse("admin:appreportes_reporteambiental_change", args=[reporte.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_administrador_tiene_el_mismo_limite_de_cinco_fotos(self):
        reporte = self.crear_reporte()
        for numero in range(5):
            Evidencia.objects.create(
                reporte=reporte, imagen=f"evidencias/foto{numero}.webp"
            )
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("appreportes:agregar_evidencia", args=[reporte.pk]),
            {"imagen": imagen_de_prueba()},
        )
        self.assertContains(respuesta, "máximo de 5 fotografías")
        self.assertEqual(reporte.evidencias.count(), 5)

    def test_responsable_no_crea_reportes(self):
        self.client.force_login(self.responsable)
        self.assertEqual(self.client.get(reverse("appreportes:crear")).status_code, 403)

    def test_propietario_edita_y_otro_ciudadano_no(self):
        reporte = self.crear_reporte()
        url = reverse("appreportes:editar", args=[reporte.pk])

        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_login(self.ciudadano)
        respuesta = self.client.post(
            url,
            self.datos_reporte(titulo="Título corregido", referencia="Otra referencia"),
        )
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

    def test_propietario_no_edita_ni_elimina_en_proceso(self):
        reporte = self.crear_reporte()
        reporte.cambiar_estado("EN_PROCESO", self.responsable)
        self.client.force_login(self.ciudadano)
        respuesta = self.client.get(
            reverse("appreportes:editar", args=[reporte.pk]), follow=True
        )
        self.assertRedirects(respuesta, reporte.get_absolute_url())
        self.assertContains(respuesta, "ya no se puede editar")
        respuesta = self.client.post(
            reverse("appreportes:eliminar", args=[reporte.pk]), follow=True
        )
        self.assertRedirects(respuesta, reporte.get_absolute_url())
        self.assertContains(respuesta, "ya no se puede eliminar")
        self.assertTrue(ReporteAmbiental.objects.filter(pk=reporte.pk).exists())

    def test_responsable_no_edita_ni_elimina(self):
        reporte = self.crear_reporte()
        self.client.force_login(self.responsable)
        self.assertEqual(
            self.client.get(
                reverse("appreportes:editar", args=[reporte.pk])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse("appreportes:eliminar", args=[reporte.pk])
            ).status_code,
            403,
        )

    def test_administrador_elimina_cualquier_reporte(self):
        reporte = self.crear_reporte()
        reporte.cambiar_estado("EN_PROCESO", self.responsable)
        self.client.force_login(self.admin)
        self.client.post(reverse("appreportes:eliminar", args=[reporte.pk]))
        self.assertFalse(ReporteAmbiental.objects.exists())

    def test_ciudadano_aporta_informacion_y_fotos_en_proceso(self):
        reporte = self.crear_reporte()
        reporte.cambiar_estado("EN_PROCESO", self.responsable)
        self.client.force_login(self.ciudadano)

        respuesta = self.client.post(
            reverse("appreportes:aportar_informacion", args=[reporte.pk]),
            {"descripcion": "Ahora también queman la basura."},
            follow=True,
        )
        self.assertContains(respuesta, "Tu información fue agregada al reporte.")
        self.assertContains(respuesta, "Aporte del ciudadano")

        self.client.post(
            reverse("appreportes:agregar_evidencia", args=[reporte.pk]),
            {"imagen": imagen_de_prueba()},
        )
        self.assertEqual(reporte.evidencias.count(), 1)

    def test_ciudadano_no_aporta_en_reporte_ajeno_ni_cerrado(self):
        reporte = self.crear_reporte()
        url_aporte = reverse("appreportes:aportar_informacion", args=[reporte.pk])

        self.client.force_login(self.otro)
        respuesta = self.client.post(
            url_aporte, {"descripcion": "Información ajena"}, follow=True
        )
        self.assertContains(
            respuesta, "Solo el autor del reporte puede agregar información."
        )
        respuesta = self.client.post(
            reverse("appreportes:agregar_evidencia", args=[reporte.pk]),
            {"imagen": imagen_de_prueba()},
            follow=True,
        )
        self.assertContains(
            respuesta, "Solo el autor del reporte puede agregar fotografías."
        )

        reporte.cambiar_estado("DESCARTADO", self.responsable, "Duplicado")
        self.client.force_login(self.ciudadano)
        respuesta = self.client.post(
            url_aporte, {"descripcion": "Caso ya cerrado"}, follow=True
        )
        self.assertRedirects(respuesta, reporte.get_absolute_url())
        self.assertContains(respuesta, "El caso ya está cerrado")
        self.assertEqual(
            reporte.seguimientos.filter(tipo="APORTE_CIUDADANO").count(), 0
        )
        self.assertEqual(reporte.evidencias.count(), 0)

    def test_descartar_sin_motivo_muestra_error(self):
        reporte = self.crear_reporte()
        self.client.force_login(self.responsable)
        url_estado = reverse("appreportes:cambiar_estado", args=[reporte.pk])

        respuesta = self.client.post(
            url_estado, {"estado": "DESCARTADO", "observacion": ""}, follow=True
        )
        self.assertContains(respuesta, "Indique el motivo")
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, ReporteAmbiental.Estado.PENDIENTE)

        respuesta = self.client.post(
            url_estado,
            {"estado": "DESCARTADO", "observacion": "Reporte duplicado"},
            follow=True,
        )
        self.assertContains(respuesta, "Reporte descartado.")
        self.assertContains(respuesta, "Reporte duplicado")

    def test_flujo_de_atencion_completo(self):
        reporte = self.crear_reporte(asignado=False)

        # El ciudadano no puede cambiar el estado ni asignar.
        self.client.force_login(self.ciudadano)
        url_estado = reverse("appreportes:cambiar_estado", args=[reporte.pk])
        self.assertEqual(
            self.client.post(url_estado, {"estado": "EN_PROCESO"}).status_code, 403
        )
        url_asignar = reverse("appreportes:asignar", args=[reporte.pk])
        self.assertEqual(
            self.client.post(
                url_asignar, {"institucion": self.institucion.pk}
            ).status_code,
            403,
        )

        # El responsable lo ve en su panel, no puede asignarlo a otra institución, lo toma y lo atiende.
        self.client.force_login(self.responsable)
        self.assertContains(
            self.client.get(reverse("appreportes:panel")), reporte.titulo
        )
        self.assertEqual(
            self.client.post(
                url_asignar, {"institucion": self.institucion.pk}
            ).status_code,
            403,
        )
        self.client.post(
            reverse("appreportes:tomar", args=[reporte.pk]), {"observacion": ""}
        )
        self.assertEqual(reporte.asignacion_activa().institucion, self.institucion)
        self.client.post(url_estado, {"estado": "EN_PROCESO"})
        self.client.post(
            reverse("appreportes:registrar_seguimiento", args=[reporte.pk]),
            {"accion": "Limpieza", "descripcion": "Se limpió el lugar."},
        )
        self.client.post(
            reverse("appreportes:agregar_evidencia", args=[reporte.pk]),
            {"imagen": imagen_de_prueba()},
        )
        respuesta = self.client.post(
            url_estado,
            {"estado": "RESUELTO", "observacion": "Caso cerrado"},
            follow=True,
        )

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
            reverse("appreportes:cambiar_estado", args=[reporte.pk]),
            {"estado": "RESUELTO"},
            follow=True,
        )
        self.assertContains(respuesta, "Registre al menos un seguimiento")

    def test_panel_de_cada_rol(self):
        self.crear_reporte()
        self.crear_reporte(usuario=self.otro)

        self.client.force_login(self.ciudadano)
        respuesta = self.client.get(reverse("appreportes:panel"))
        self.assertContains(respuesta, "Mis reportes")
        self.assertEqual(respuesta.context["page_obj"].paginator.count, 1)

        self.client.force_login(self.responsable)
        respuesta = self.client.get(reverse("appreportes:panel"))
        self.assertContains(respuesta, "Casos de mi institución")
        self.assertEqual(respuesta.context["page_obj"].paginator.count, 2)

        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("appreportes:panel"))
        self.assertContains(respuesta, "Todos los reportes")
        self.assertEqual(respuesta.context["page_obj"].paginator.count, 2)

    def test_filtros(self):
        self.crear_reporte()
        respuesta = self.client.get(
            reverse("appreportes:lista"), {"nivel_gravedad": "ALTO"}
        )
        self.assertEqual(respuesta.context["page_obj"].paginator.count, 0)
        respuesta = self.client.get(
            reverse("appreportes:lista"), {"buscar": "basura", "estado": "PENDIENTE"}
        )
        self.assertEqual(respuesta.context["page_obj"].paginator.count, 1)

    # --- Validación de textos: alertas debajo de cada campo, sin páginas de error ---

    def test_datos_invalidos_muestran_alertas_bajo_cada_campo(self):
        self.client.force_login(self.ciudadano)
        respuesta = self.client.post(
            reverse("appreportes:crear"),
            self.datos_reporte(
                titulo="x#$%&@",
                descripcion="123456789 asdfghjkl 987654321",
                referencia="12345",
            ),
        )
        self.assertEqual(respuesta.status_code, 200)
        errores = respuesta.context["form"].errors
        self.assertIn("titulo", errores)
        self.assertIn("descripcion", errores)
        self.assertIn("referencia", errores)
        self.assertContains(respuesta, "No se permiten estos caracteres")
        self.assertContains(respuesta, "No escriba más de 8 números seguidos.")
        self.assertContains(respuesta, "El texto debe incluir letras")
        self.assertFalse(ReporteAmbiental.objects.exists())

    def test_descripcion_corta_de_tres_palabras_es_valida(self):
        self.client.force_login(self.ciudadano)
        self.client.post(
            reverse("appreportes:crear"),
            self.datos_reporte(descripcion="Basura en el río"),
        )
        self.assertTrue(
            ReporteAmbiental.objects.filter(descripcion="Basura en el río").exists()
        )

    def test_seguimiento_invalido_muestra_alerta_en_el_detalle(self):
        reporte = self.crear_reporte()
        self.client.force_login(self.responsable)
        respuesta = self.client.post(
            reverse("appreportes:registrar_seguimiento", args=[reporte.pk]),
            {"accion": "@@@@", "descripcion": "sdfgh qwrtp"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "No se permiten estos caracteres")
        self.assertContains(respuesta, "no parece una palabra")
        self.assertEqual(reporte.seguimientos.count(), 0)

    def test_aporte_invalido_no_se_guarda(self):
        reporte = self.crear_reporte()
        self.client.force_login(self.ciudadano)
        respuesta = self.client.post(
            reverse("appreportes:aportar_informacion", args=[reporte.pk]),
            {"descripcion": "1234567890123"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "No escriba más de 8 números seguidos.")
        self.assertEqual(reporte.seguimientos.count(), 0)

    def test_reporte_inexistente_vuelve_a_la_lista_con_aviso(self):
        respuesta = self.client.get(
            reverse("appreportes:detalle", args=[99999]), follow=True
        )
        self.assertRedirects(respuesta, reverse("appreportes:lista"))
        self.assertContains(
            respuesta, "El reporte que buscas no existe o fue eliminado."
        )

        self.client.force_login(self.admin)
        for nombre in ("editar", "eliminar"):
            with self.subTest(vista=nombre):
                respuesta = self.client.get(
                    reverse(f"appreportes:{nombre}", args=[99999])
                )
                self.assertRedirects(respuesta, reverse("appreportes:lista"))
        respuesta = self.client.post(
            reverse("appreportes:cambiar_estado", args=[99999]),
            {"estado": "EN_PROCESO"},
        )
        self.assertRedirects(respuesta, reverse("appreportes:lista"))

    # --- Volver «Atrás», recargar o abrir como página una dirección de formulario ---

    def test_acciones_del_detalle_abiertas_como_pagina_llevan_al_detalle(self):
        reporte = self.crear_reporte()
        self.client.force_login(self.responsable)
        for nombre in (
            "agregar_evidencia",
            "cambiar_estado",
            "registrar_seguimiento",
            "aportar_informacion",
            "asignar",
            "tomar",
        ):
            with self.subTest(accion=nombre):
                respuesta = self.client.get(
                    reverse(f"appreportes:{nombre}", args=[reporte.pk])
                )
                self.assertRedirects(respuesta, reporte.get_absolute_url())
        self.assertEqual(reporte.seguimientos.count(), 0)
        self.assertEqual(reporte.evidencias.count(), 0)

    def test_volver_de_iniciar_sesion_a_una_accion_lleva_al_detalle(self):
        # La sesión se cerró en otra pestaña: el formulario del detalle manda a iniciar sesión y, al entrar,
        # el navegador abre la dirección de la acción como página.
        reporte = self.crear_reporte()
        url_accion = reverse("appreportes:registrar_seguimiento", args=[reporte.pk])
        respuesta = self.client.post(
            url_accion, {"accion": "Inspección", "descripcion": "Se visitó el lugar."}
        )
        self.assertRedirects(
            respuesta, f"{reverse('appusuarios:ingresar')}?next={url_accion}"
        )
        self.client.force_login(self.responsable)
        respuesta = self.client.get(url_accion)
        self.assertRedirects(respuesta, reporte.get_absolute_url())

    def test_pagina_con_errores_no_pide_reenviar_el_formulario(self):
        self.client.force_login(self.ciudadano)
        con_errores = self.client.post(
            reverse("appreportes:crear"), self.datos_reporte(titulo="x")
        )
        self.assertEqual(con_errores.status_code, 200)
        self.assertContains(con_errores, "history.replaceState")
        # Las páginas abiertas normalmente no llevan el script.
        self.assertNotContains(
            self.client.get(reverse("appreportes:crear")), "history.replaceState"
        )

    def test_listas_de_seleccion_en_espanol(self):
        self.client.force_login(self.ciudadano)
        respuesta = self.client.get(reverse("appreportes:crear"))
        # Categoría, comunidad y nivel de gravedad.
        self.assertContains(respuesta, "- Seleccione una opción -", count=3)
        self.assertNotContains(respuesta, "Select an option")
        # «Asignar a una institución» (administrador) en el detalle del reporte.
        self.client.force_login(self.admin)
        respuesta = self.client.get(self.crear_reporte().get_absolute_url())
        self.assertContains(respuesta, "- Seleccione una opción -")
        self.assertNotContains(respuesta, "Select an option")
        # El panel de administración (formulario para agregar un reporte).
        Administrador.objects.filter(pk=self.admin.pk).update(
            is_staff=True, is_superuser=True
        )
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("admin:appreportes_reporteambiental_add"))
        self.assertContains(respuesta, "- Seleccione una opción -")
        self.assertNotContains(respuesta, "Select an option")

    # --- Volver «Atrás» después de guardar un reporte y guardar otra vez ---

    def test_volver_atras_y_guardar_otra_vez_no_duplica_el_reporte(self):
        self.client.force_login(self.ciudadano)
        url = reverse("appreportes:crear")
        self.client.post(url, self.datos_reporte(token_envio=str(uuid.uuid4())))
        reporte = ReporteAmbiental.objects.get()
        # La página recargada al volver «Atrás» trae un código nuevo, pero los mismos datos.
        respuesta = self.client.post(
            url, self.datos_reporte(token_envio=str(uuid.uuid4())), follow=True
        )
        self.assertRedirects(respuesta, reporte.get_absolute_url())
        self.assertContains(respuesta, "Este reporte ya se había guardado")
        self.assertEqual(ReporteAmbiental.objects.count(), 1)

    def test_otro_reporte_con_datos_distintos_si_se_guarda(self):
        self.client.force_login(self.ciudadano)
        url = reverse("appreportes:crear")
        self.client.post(url, self.datos_reporte(token_envio=str(uuid.uuid4())))
        self.client.post(
            url,
            self.datos_reporte(
                token_envio=str(uuid.uuid4()), titulo="Basura quemada en el parque"
            ),
        )
        self.assertEqual(ReporteAmbiental.objects.count(), 2)

    def test_el_mismo_problema_se_puede_reportar_pasados_los_minutos(self):
        self.client.force_login(self.ciudadano)
        url = reverse("appreportes:crear")
        self.client.post(url, self.datos_reporte(token_envio=str(uuid.uuid4())))
        ReporteAmbiental.objects.update(
            fecha_creacion=timezone.now() - timedelta(minutes=11)
        )
        self.client.post(url, self.datos_reporte(token_envio=str(uuid.uuid4())))
        self.assertEqual(ReporteAmbiental.objects.count(), 2)

    def test_otro_ciudadano_puede_reportar_lo_mismo(self):
        url = reverse("appreportes:crear")
        for usuario in (self.ciudadano, self.otro):
            self.client.force_login(usuario)
            self.client.post(url, self.datos_reporte(token_envio=str(uuid.uuid4())))
        self.assertEqual(ReporteAmbiental.objects.count(), 2)

    def test_formulario_nuevo_reporte_no_se_guarda_en_la_cache_del_navegador(self):
        self.client.force_login(self.ciudadano)
        respuesta = self.client.get(reverse("appreportes:crear"))
        self.assertIn("no-store", respuesta["Cache-Control"])

    # --- Información sobre el ambiente en la pantalla de inicio ---

    def test_inicio_muestra_la_informacion_del_ambiente(self):
        from django.contrib.staticfiles import finders

        respuesta = self.client.get(reverse("appreportes:inicio"))
        self.assertContains(respuesta, "Cuidemos el medio ambiente en El Salvador")
        for titulo in (
            "No quemes la basura",
            "Ríos y quebradas limpios",
            "Evita criaderos de zancudos",
            "Cómo hacer un buen reporte",
        ):
            self.assertContains(respuesta, titulo)
        self.assertContains(respuesta, "/static/js/aparecer.js")
        self.assertIsNotNone(
            finders.find("js/aparecer.js"), "No existe static/js/aparecer.js"
        )

    # --- El responsable y el administrador cambian el estado del mismo reporte a la vez ---

    def test_se_queda_el_primer_cambio_de_estado(self):
        reporte = self.crear_reporte()
        # El administrador abrió el reporte cuando estaba pendiente.
        copia_del_admin = ReporteAmbiental.objects.get(pk=reporte.pk)
        reporte.cambiar_estado("EN_PROCESO", self.responsable)
        with self.assertRaisesMessage(
            ValidationError, "otro usuario ya lo cambió a «En proceso»"
        ):
            copia_del_admin.cambiar_estado(
                "DESCARTADO", self.admin, "Reporte duplicado", estado_visto="PENDIENTE"
            )
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, "EN_PROCESO")
        self.assertEqual(reporte.historial.count(), 1)

    def test_el_estado_se_valida_con_el_valor_real_de_la_base_de_datos(self):
        # Aunque no se indique el estado visto, la transición se revisa con el estado ya guardado.
        reporte = self.crear_reporte()
        copia_vieja = ReporteAmbiental.objects.get(pk=reporte.pk)
        reporte.cambiar_estado("EN_PROCESO", self.responsable)
        with self.assertRaisesMessage(
            ValidationError, "No se permite pasar de En proceso a En proceso"
        ):
            copia_vieja.cambiar_estado("EN_PROCESO", self.admin)
        self.assertEqual(reporte.historial.count(), 1)

    def test_el_segundo_ve_aviso_y_el_estado_actual(self):
        reporte = self.crear_reporte()
        detalle = reporte.get_absolute_url()
        self.client.force_login(self.admin)
        self.assertContains(
            self.client.get(detalle), 'name="estado_visto" value="PENDIENTE"'
        )
        # Mientras tanto, el responsable lo pasa a «En proceso».
        reporte.cambiar_estado("EN_PROCESO", self.responsable)
        respuesta = self.client.post(
            reverse("appreportes:cambiar_estado", args=[reporte.pk]),
            {
                "estado": "DESCARTADO",
                "observacion": "Reporte duplicado",
                "estado_visto": "PENDIENTE",
            },
            follow=True,
        )
        self.assertRedirects(respuesta, detalle)
        self.assertContains(
            respuesta, "otro usuario ya lo cambió a «En proceso» mientras lo revisabas"
        )
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, "EN_PROCESO")
        self.assertEqual(reporte.historial.count(), 1)
        # La página recargada ya trae el estado actual en el formulario.
        self.assertContains(respuesta, 'name="estado_visto" value="EN_PROCESO"')

    def test_cambio_de_estado_normal_sigue_funcionando(self):
        reporte = self.crear_reporte()
        self.client.force_login(self.responsable)
        self.client.post(
            reverse("appreportes:cambiar_estado", args=[reporte.pk]),
            {"estado": "EN_PROCESO", "observacion": "", "estado_visto": "PENDIENTE"},
        )
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, "EN_PROCESO")

    # --- Un responsable por institución: cada uno atiende solo los casos de su institución ---

    def otra_institucion_con_responsable(self):
        marn = Institucion.objects.create(nombre="MARN", tipo=Institucion.Tipo.GOBIERNO)
        responsable_marn = Responsable.objects.create_user(
            "marn@eco.sv", "marn@eco.sv", "clave-segura-1", institucion=marn
        )
        return marn, responsable_marn

    def test_responsable_no_atiende_casos_de_otra_institucion(self):
        reporte = self.crear_reporte()  # Asignado a la alcaldía.
        _, responsable_marn = self.otra_institucion_con_responsable()
        self.client.force_login(responsable_marn)
        detalle = self.client.get(reporte.get_absolute_url())
        self.assertContains(
            detalle,
            "Este caso lo atiende Alcaldía; solo su responsable puede actualizarlo.",
        )
        self.assertNotContains(detalle, "Cambiar estado")
        self.assertNotContains(detalle, "Registrar seguimiento")
        self.assertNotContains(detalle, "Agregar fotografía")
        # Aunque envíe el formulario a mano, vuelve al detalle con el aviso y no se guarda nada.
        respuesta = self.client.post(
            reverse("appreportes:cambiar_estado", args=[reporte.pk]),
            {"estado": "EN_PROCESO", "observacion": "", "estado_visto": "PENDIENTE"},
            follow=True,
        )
        self.assertRedirects(respuesta, reporte.get_absolute_url())
        self.assertContains(respuesta, "Este caso lo atiende Alcaldía")
        self.client.post(
            reverse("appreportes:registrar_seguimiento", args=[reporte.pk]),
            {"accion": "Inspección", "descripcion": "Se visitó el lugar."},
        )
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, "PENDIENTE")
        self.assertEqual(reporte.seguimientos.count(), 0)

    def test_panel_del_responsable_muestra_su_institucion_y_los_casos_sin_asignar(self):
        propio = self.crear_reporte()
        sin_asignar = self.crear_reporte(asignado=False)
        de_otra = self.crear_reporte(asignado=False)
        marn, _ = self.otra_institucion_con_responsable()
        de_otra.asignar_a(marn, self.admin)
        self.client.force_login(self.responsable)
        reportes = list(
            self.client.get(reverse("appreportes:panel")).context["reportes"]
        )
        self.assertIn(propio, reportes)
        self.assertIn(sin_asignar, reportes)
        self.assertNotIn(de_otra, reportes)

    def test_responsable_toma_un_caso_sin_asignar(self):
        reporte = self.crear_reporte(asignado=False)
        self.client.force_login(self.responsable)
        detalle = self.client.get(reporte.get_absolute_url())
        self.assertContains(detalle, "Tomar este caso")
        self.assertNotContains(
            detalle, "Cambiar estado"
        )  # Antes de tomarlo, no lo atiende.
        respuesta = self.client.post(
            reverse("appreportes:tomar", args=[reporte.pk]),
            {"observacion": "Se visitará el lugar."},
            follow=True,
        )
        self.assertContains(respuesta, "Tomaste el caso para tu institución")
        self.assertContains(respuesta, "Cambiar estado")
        self.assertNotContains(respuesta, "Tomar este caso")
        self.assertEqual(reporte.asignacion_activa().institucion, self.institucion)

    def test_si_dos_toman_el_mismo_caso_se_queda_el_primero(self):
        reporte = self.crear_reporte(asignado=False)
        _, responsable_marn = self.otra_institucion_con_responsable()
        # Los dos abrieron el caso cuando nadie lo había tomado; la alcaldía lo toma primero.
        reporte.tomar(self.responsable)
        self.client.force_login(responsable_marn)
        respuesta = self.client.post(
            reverse("appreportes:tomar", args=[reporte.pk]),
            {"observacion": ""},
            follow=True,
        )
        self.assertRedirects(respuesta, reporte.get_absolute_url())
        self.assertContains(
            respuesta, "No se pudo tomar el caso: ya lo atiende Alcaldía."
        )
        self.assertEqual(reporte.asignaciones.filter(activa=True).count(), 1)
        self.assertEqual(reporte.asignacion_activa().institucion, self.institucion)

    def test_no_se_toma_un_caso_cerrado(self):
        reporte = self.crear_reporte(asignado=False)
        reporte.cambiar_estado("DESCARTADO", self.admin, "Reporte duplicado")
        self.client.force_login(self.responsable)
        self.assertNotContains(
            self.client.get(reporte.get_absolute_url()), "Tomar este caso"
        )
        respuesta = self.client.post(
            reverse("appreportes:tomar", args=[reporte.pk]),
            {"observacion": ""},
            follow=True,
        )
        self.assertContains(respuesta, "ya está cerrado")
        self.assertIsNone(reporte.asignacion_activa())

    def test_reasignado_mientras_lo_atendia_vuelve_al_detalle_con_aviso(self):
        reporte = self.crear_reporte()
        marn, _ = self.otra_institucion_con_responsable()
        self.client.force_login(self.responsable)
        self.assertContains(
            self.client.get(reporte.get_absolute_url()), "Cambiar estado"
        )
        # Mientras tenía la página abierta, el administrador lo pasó al MARN.
        reporte.asignar_a(marn, self.admin)
        for nombre, datos in (
            (
                "cambiar_estado",
                {
                    "estado": "EN_PROCESO",
                    "observacion": "",
                    "estado_visto": "PENDIENTE",
                },
            ),
            (
                "registrar_seguimiento",
                {"accion": "Inspección", "descripcion": "Se visitó el lugar."},
            ),
            ("agregar_evidencia", {"imagen": imagen_de_prueba()}),
        ):
            with self.subTest(accion=nombre):
                respuesta = self.client.post(
                    reverse(f"appreportes:{nombre}", args=[reporte.pk]),
                    datos,
                    follow=True,
                )
                self.assertRedirects(respuesta, reporte.get_absolute_url())
                self.assertContains(respuesta, "Este caso lo atiende MARN")
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, "PENDIENTE")
        self.assertEqual(reporte.seguimientos.count(), 0)
        self.assertEqual(reporte.evidencias.count(), 0)

    def test_administrador_asigna_y_reasigna(self):
        reporte = self.crear_reporte(asignado=False)
        marn, _ = self.otra_institucion_con_responsable()
        self.client.force_login(self.admin)
        url = reverse("appreportes:asignar", args=[reporte.pk])
        self.client.post(url, {"institucion": self.institucion.pk, "observacion": ""})
        self.client.post(url, {"institucion": marn.pk, "observacion": ""})
        self.assertEqual(reporte.asignaciones.filter(activa=True).count(), 1)
        self.assertEqual(reporte.asignacion_activa().institucion, marn)

    # --- Página del error 500 y páginas privadas sin copia en el navegador ---

    def test_pagina_del_error_500(self):
        from django.template.loader import render_to_string

        # Se dibuja sin datos de la página (como lo hace Django cuando hay un error).
        html = render_to_string("500.html")
        self.assertIn("Algo salió mal", html)
        self.assertIn('href="/"', html)

    def test_paginas_privadas_no_se_guardan_en_el_navegador(self):
        reporte = self.crear_reporte()
        self.client.force_login(self.ciudadano)
        for url in (
            reverse("appreportes:panel"),
            reverse("appusuarios:perfil"),
            reporte.get_absolute_url(),
            reverse("appreportes:inicio"),
        ):
            with self.subTest(url=url):
                self.assertIn("no-store", self.client.get(url)["Cache-Control"])

    def test_paginas_de_visitantes_no_cambian(self):
        reporte = self.crear_reporte()
        for url in (
            reverse("appreportes:inicio"),
            reverse("appreportes:lista"),
            reporte.get_absolute_url(),
        ):
            with self.subTest(url=url):
                self.assertFalse(self.client.get(url).has_header("Cache-Control"))

    def test_al_cerrar_sesion_y_volver_a_mi_perfil_pide_iniciar_sesion(self):
        self.client.force_login(self.ciudadano)
        self.assertIn(
            "no-store", self.client.get(reverse("appusuarios:perfil"))["Cache-Control"]
        )
        self.client.post(reverse("appusuarios:salir"))
        respuesta = self.client.get(reverse("appusuarios:perfil"))
        self.assertRedirects(
            respuesta,
            f"{reverse('appusuarios:ingresar')}?next={reverse('appusuarios:perfil')}",
        )

    # --- Fondos animados (decorativos) ---

    def test_fondos_animados_en_inicio_ingreso_y_registro(self):
        inicio = self.client.get(reverse("appreportes:inicio"))
        self.assertContains(inicio, 'class="eco-ola" aria-hidden="true"')
        self.assertContains(inicio, 'class="eco-fondo" aria-hidden="true"')
        for nombre in ("appusuarios:ingresar", "appusuarios:registro"):
            with self.subTest(pagina=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertContains(respuesta, "eco-fondo-suave")
                self.assertContains(respuesta, 'class="eco-fondo" aria-hidden="true"')
                self.assertContains(
                    respuesta, 'type="submit"'
                )  # El formulario sigue igual.
        # Las demás pantallas no llevan fondo animado.
        self.client.force_login(self.ciudadano)
        self.assertNotContains(
            self.client.get(reverse("appreportes:crear")), "eco-fondo"
        )

    # --- Botón «Contacto» y panel de contacto ---

    def test_boton_y_panel_de_contacto_en_todas_las_paginas(self):
        reporte = self.crear_reporte()
        paginas = [
            reverse("appreportes:inicio"),
            reverse("appreportes:lista"),
            reporte.get_absolute_url(),
            reverse("appusuarios:ingresar"),
            reverse("appusuarios:registro"),
        ]
        for url in paginas:
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                # El botón apunta al panel, y el panel empieza cerrado.
                self.assertContains(respuesta, 'id="eco-boton-contacto"')
                self.assertContains(respuesta, 'aria-controls="eco-contacto"')
                self.assertContains(respuesta, 'id="eco-contacto" class="eco-contacto"')
                self.assertContains(respuesta, 'aria-hidden="true"')
                for dato in ("Correo:", "Teléfono:", "Dirección:"):
                    self.assertContains(respuesta, dato)
                self.assertContains(respuesta, "/static/js/contacto.js")
        # También con sesión iniciada (la barra cambia).
        self.client.force_login(self.ciudadano)
        self.assertContains(
            self.client.get(reverse("appreportes:panel")), 'id="eco-boton-contacto"'
        )

    def test_estilos_y_scripts_llevan_su_version(self):
        # Así el navegador descarga la versión nueva cada vez que el archivo cambia, sin Ctrl + F5.
        import re

        html = self.client.get(reverse("appreportes:inicio")).content.decode()
        for archivo in ("css/estilos.css", "js/aparecer.js", "js/contacto.js"):
            with self.subTest(archivo=archivo):
                self.assertRegex(html, rf"/static/{re.escape(archivo)}\?v=\d+")

    def test_correo_de_contacto_abre_gmail_para_escribir(self):
        respuesta = self.client.get(reverse("appreportes:inicio"))
        self.assertContains(
            respuesta,
            'href="https://mail.google.com/mail/?view=cm&amp;fs=1&amp;to=ecoreporte2026@gmail.com'
            '&amp;su=Consulta%20desde%20EcoReporte%20Comunitario">ecoreporte2026@gmail.com</a>',
        )
        self.assertContains(respuesta, 'target="_blank" rel="noopener"')
        self.assertNotContains(respuesta, "mailto:")
        self.assertNotContains(respuesta, "Copiar correo")
        # Los datos van en el lado derecho, pero alineados a la izquierda entre sí (ya no text-md-end).
        self.assertContains(respuesta, 'class="eco-contacto-datos"')
        self.assertNotContains(respuesta, "text-md-end")
