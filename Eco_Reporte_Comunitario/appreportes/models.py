import os

from datetime import datetime, timedelta
from functools import reduce
from operator import or_

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.db.models import F, Q
from django.db.models.functions import Cast, Now
from django.urls import reverse
from django.utils import timezone

from Eco_Reporte_Comunitario.modelos_base import ModeloBase
from Eco_Reporte_Comunitario.restricciones import (
    ANIOS_MAXIMOS_INCIDENTE,
    MAXIMO_EVIDENCIAS_POR_REPORTE,
    MINIMO_ACCION_SEGUIMIENTO,
    MINIMO_DESCRIPCION_CATEGORIA,
    MINIMO_DESCRIPCION_FOTO,
    MINIMO_DESCRIPCION_REPORTE,
    MINIMO_DESCRIPCION_SEGUIMIENTO,
    MINIMO_OBSERVACION,
    MINIMO_TITULO_REPORTE,
    MINUTOS_REPORTE_DUPLICADO,
    RestarAnios,
    q_contiene_letras,
    q_nombre_general,
    q_texto_libre,
    q_texto_libre_opcional,
    q_valor_en,
    restar_anios,
    validador_texto,
    validar_nombre_general,
)


MENSAJE_FECHA_MUY_ANTIGUA = (
    f"La fecha del incidente no puede ser de hace más de {ANIOS_MAXIMOS_INCIDENTE} años."
)


class NivelGravedad(models.TextChoices):
    BAJO = "BAJO", "Bajo"
    MEDIO = "MEDIO", "Medio"
    ALTO = "ALTO", "Alto"


class EstadoReporte(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    EN_PROCESO = "EN_PROCESO", "En proceso"
    RESUELTO = "RESUELTO", "Resuelto"
    DESCARTADO = "DESCARTADO", "Descartado"


class TipoSeguimiento(models.TextChoices):
    SEGUIMIENTO = "SEGUIMIENTO", "Seguimiento"
    APORTE_CIUDADANO = "APORTE_CIUDADANO", "Aporte del ciudadano"


class CategoriaProblema(ModeloBase):
    """Entidad 6."""

    nombre = models.CharField(max_length=100, unique=True, validators=[validar_nombre_general])
    descripcion = models.CharField(
        "descripción", max_length=250, validators=[validador_texto(MINIMO_DESCRIPCION_CATEGORIA)]
    )
    activa = models.BooleanField(default=True, db_default=True)

    class Meta:
        verbose_name = "categoría de problema"
        verbose_name_plural = "categorías de problema"
        ordering = ["nombre"]
        constraints = [
            models.CheckConstraint(
                condition=q_nombre_general("nombre"),
                name="ck_categoria_nombre_valido",
                violation_error_message="El nombre de la categoría solo admite letras, números y signos básicos.",
            ),
            models.CheckConstraint(
                condition=q_texto_libre("descripcion", MINIMO_DESCRIPCION_CATEGORIA),
                name="ck_categoria_descripcion_valida",
                violation_error_message=(
                    f"La descripción de la categoría debe tener al menos {MINIMO_DESCRIPCION_CATEGORIA[0]} "
                    "caracteres, incluir letras y no llevar símbolos raros."
                ),
            ),
        ]

    def __str__(self):
        return self.nombre


class ReporteQuerySet(models.QuerySet):
    def filtrar(self, categoria=None, estado=None, nivel_gravedad=None, comunidad=None, buscar=None):
        """RF11: filtra por cualquier combinación de criterios."""
        consulta = self
        if buscar:
            consulta = consulta.filter(models.Q(titulo__icontains=buscar) | models.Q(descripcion__icontains=buscar))
        if categoria:
            consulta = consulta.filter(categoria=categoria)
        if estado:
            consulta = consulta.filter(estado=estado)
        if nivel_gravedad:
            consulta = consulta.filter(nivel_gravedad=nivel_gravedad)
        if comunidad:
            consulta = consulta.filter(ubicacion__comunidad=comunidad)
        return consulta

    def activos(self):
        return self.filter(estado__in=ReporteAmbiental.ESTADOS_ACTIVOS)

    def criticos(self):
        return self.activos().filter(nivel_gravedad=ReporteAmbiental.NivelGravedad.ALTO)

    def duplicado_reciente(self, usuario, datos):
        """El reporte que este usuario acaba de guardar con los mismos datos, si existe.

        Detecta el formulario enviado otra vez al volver «Atrás»: el navegador vuelve a pedir la página,
        trae un código de envío nuevo y rellena los campos con lo que se había escrito.
        """
        hace_poco = timezone.now() - timedelta(minutes=MINUTOS_REPORTE_DUPLICADO)
        return self.filter(
            usuario=usuario,
            categoria=datos.get("categoria"),
            titulo=datos.get("titulo"),
            descripcion=datos.get("descripcion"),
            fecha_incidente=datos.get("fecha_incidente"),
            fecha_creacion__gte=hace_poco,
        ).first()


class ReporteAmbiental(ModeloBase):
    """Entidad 7. El estado solo puede cambiarse con cambiar_estado()."""

    NivelGravedad = NivelGravedad
    Estado = EstadoReporte

    # Transiciones permitidas. Desde RESUELTO y DESCARTADO solo se puede reabrir el caso.
    TRANSICIONES = {
        Estado.PENDIENTE: {Estado.EN_PROCESO, Estado.DESCARTADO},
        Estado.EN_PROCESO: {Estado.RESUELTO, Estado.DESCARTADO},
        Estado.RESUELTO: {Estado.EN_PROCESO},
        Estado.DESCARTADO: {Estado.PENDIENTE},
    }

    # Casos que siguen abiertos: el ciudadano aún puede agregar fotos e información.
    ESTADOS_ACTIVOS = (Estado.PENDIENTE, Estado.EN_PROCESO)

    MAXIMO_EVIDENCIAS = MAXIMO_EVIDENCIAS_POR_REPORTE

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reportes")
    categoria = models.ForeignKey(
        CategoriaProblema, on_delete=models.PROTECT, related_name="reportes", verbose_name="categoría"
    )
    ubicacion = models.ForeignKey(
        "appterritorio.Ubicacion", on_delete=models.PROTECT, related_name="reportes", verbose_name="ubicación"
    )
    titulo = models.CharField("título", max_length=150, validators=[validador_texto(MINIMO_TITULO_REPORTE)])
    descripcion = models.CharField(
        "descripción", max_length=1000, validators=[validador_texto(MINIMO_DESCRIPCION_REPORTE)]
    )
    fecha_incidente = models.DateField("fecha del incidente")
    nivel_gravedad = models.CharField(max_length=10, choices=NivelGravedad.choices)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        db_default=Estado.PENDIENTE,
        editable=False,
    )
    # Código único de cada formulario de "Nuevo reporte": si se envía dos veces (doble clic),
    # SQL Server rechaza el segundo y no se crea un reporte duplicado.
    token_envio = models.UUIDField("código de envío", null=True, blank=True, editable=False)

    objects = ReporteQuerySet.as_manager()

    _cambio_estado_autorizado = False

    class Meta:
        verbose_name = "reporte ambiental"
        verbose_name_plural = "reportes ambientales"
        ordering = ["-fecha_creacion"]
        # Índices para los filtros y el orden más usados (las llaves foráneas ya tienen el suyo).
        indexes = [
            models.Index(fields=["estado", "-fecha_creacion"], name="ix_reporte_estado_fecha"),
            models.Index(fields=["-fecha_creacion"], name="ix_reporte_fecha"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=q_texto_libre("titulo", MINIMO_TITULO_REPORTE),
                name="ck_reporte_titulo_valido",
                violation_error_message=(
                    f"El título debe tener al menos {MINIMO_TITULO_REPORTE[0]} caracteres, "
                    "incluir letras y no llevar símbolos raros ni cadenas largas de números."
                ),
            ),
            models.CheckConstraint(
                condition=q_texto_libre("descripcion", MINIMO_DESCRIPCION_REPORTE),
                name="ck_reporte_descripcion_valida",
                violation_error_message=(
                    f"La descripción debe tener al menos {MINIMO_DESCRIPCION_REPORTE[0]} caracteres, "
                    "incluir letras y no llevar símbolos raros ni cadenas largas de números."
                ),
            ),
            models.CheckConstraint(
                condition=Q(fecha_incidente__lte=Cast(Now(), models.DateField())),
                name="ck_reporte_fecha_no_futura",
                violation_error_message="La fecha del incidente no puede ser futura.",
            ),
            # Se compara con la fecha de creación (y no con hoy) para que el reporte se pueda seguir
            # actualizando años después sin que SQL Server lo rechace.
            models.CheckConstraint(
                condition=Q(
                    fecha_incidente__gte=RestarAnios(
                        Cast(F("fecha_creacion"), models.DateField()), ANIOS_MAXIMOS_INCIDENTE
                    )
                ),
                name="ck_reporte_fecha_antiguedad_maxima",
                violation_error_message=MENSAJE_FECHA_MUY_ANTIGUA,
            ),
            models.UniqueConstraint(
                fields=["token_envio"],
                condition=Q(token_envio__isnull=False),
                name="uq_reporte_token_envio",
                violation_error_message="Este reporte ya se había guardado.",
            ),
            models.CheckConstraint(
                condition=q_valor_en("nivel_gravedad", NivelGravedad.choices),
                name="ck_reporte_gravedad_valida",
                violation_error_message="El nivel de gravedad no es válido.",
            ),
            models.CheckConstraint(
                condition=q_valor_en("estado", EstadoReporte.choices),
                name="ck_reporte_estado_valido",
                violation_error_message="El estado del reporte no es válido.",
            ),
        ]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("appreportes:detalle", args=[self.pk])

    def fecha_minima_incidente(self):
        """ANIOS_MAXIMOS_INCIDENTE (5) años antes de la fecha en que se creó el reporte (o de hoy, si aún no se guarda).

        Usa la misma fecha que compara SQL Server en ck_reporte_fecha_antiguedad_maxima.
        """
        # En un reporte nuevo, fecha_creacion aún no es una fecha (la pondrá la base de datos).
        creado = self.fecha_creacion if isinstance(self.fecha_creacion, datetime) else timezone.now()
        return restar_anios(creado.date(), ANIOS_MAXIMOS_INCIDENTE)

    def clean(self):
        super().clean()
        if self.fecha_incidente and self.fecha_incidente < self.fecha_minima_incidente():
            raise ValidationError({
                "fecha_incidente": (
                    f"{MENSAJE_FECHA_MUY_ANTIGUA[:-1]} "
                    f"(la más antigua permitida es el {self.fecha_minima_incidente():%d/%m/%Y})."
                )
            })

    def save(self, *args, **kwargs):
        if self.pk and not self._cambio_estado_autorizado:
            guardado = type(self).objects.filter(pk=self.pk).values_list("estado", flat=True).first()
            if guardado is not None and guardado != self.estado:
                raise ValidationError("El estado solo puede modificarse mediante cambiar_estado().")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Las evidencias se borran en cascada; aquí se eliminan también sus archivos.
        for evidencia in self.evidencias.all():
            evidencia.imagen.delete(save=False)
        return super().delete(*args, **kwargs)

    # --- Reglas de acceso: cada vista pregunta al reporte qué puede hacer el usuario ---

    def es_propietario(self, usuario):
        return usuario.is_authenticated and self.usuario_id == usuario.pk

    def esta_activo(self):
        """Pendiente o En proceso: el caso sigue abierto."""
        return self.estado in self.ESTADOS_ACTIVOS

    def puede_modificar(self, usuario):
        """El ciudadano solo edita su reporte mientras está pendiente; el administrador, cualquiera."""
        if not usuario.is_authenticated:
            return False
        if usuario.puede("modificar_cualquier_reporte"):
            return True
        return (
            self.es_propietario(usuario)
            and usuario.puede("modificar_reporte_propio")
            and self.estado == self.Estado.PENDIENTE
        )

    def puede_eliminar(self, usuario):
        """El ciudadano solo elimina su reporte mientras está pendiente; el administrador, cualquiera."""
        if not usuario.is_authenticated:
            return False
        if usuario.puede("eliminar_cualquier_reporte"):
            return True
        return (
            self.es_propietario(usuario)
            and usuario.puede("eliminar_reporte_propio")
            and self.estado == self.Estado.PENDIENTE
        )

    def atendido_por_institucion_de(self, usuario):
        """El caso está asignado (asignación activa) a la institución de este usuario."""
        institucion_id = getattr(usuario, "institucion_id", None)
        return bool(institucion_id) and self.asignaciones.filter(activa=True, institucion_id=institucion_id).exists()

    def puede_gestionar(self, usuario):
        """Cambiar estado, registrar seguimiento y subir fotos del avance: el responsable de la institución
        a la que está asignado el caso, o el administrador."""
        if not (usuario.is_authenticated and usuario.puede("cambiar_estado")):
            return False
        return usuario.puede("gestionar_cualquier_reporte") or self.atendido_por_institucion_de(usuario)

    def motivo_no_gestiona(self):
        """Explicación para un responsable que ve un caso que no le toca atender."""
        asignacion = self.asignacion_activa()
        if asignacion is None:
            return "Este caso todavía no está asignado a tu institución. Tómalo primero para poder atenderlo."
        return f"Este caso lo atiende {asignacion.institucion}; solo su responsable puede actualizarlo."

    def puede_asignar(self, usuario):
        """Asignar o reasignar a una institución: solo el administrador, mientras el caso está abierto."""
        return usuario.is_authenticated and usuario.puede("asignar_reporte") and self.esta_activo()

    def puede_tomar(self, usuario):
        """Un responsable toma, para su institución, un caso abierto que nadie ha tomado todavía."""
        return (
            usuario.is_authenticated
            and usuario.puede("tomar_reporte")
            and bool(usuario.institucion_id)
            and usuario.institucion.activa
            and self.esta_activo()
            and not self.asignaciones.filter(activa=True).exists()
        )

    def puede_agregar_evidencia(self, usuario):
        """El responsable de la institución asignada y el administrador siempre; el dueño solo mientras
        el caso está abierto."""
        if self.puede_gestionar(usuario):
            return True
        return self.es_propietario(usuario) and usuario.puede("agregar_evidencia") and self.esta_activo()

    def puede_aportar_informacion(self, usuario):
        """Solo el dueño del reporte, mientras el caso está abierto."""
        return self.es_propietario(usuario) and usuario.puede("aportar_informacion") and self.esta_activo()

    def tiene_seguimiento_registrado(self):
        """Los aportes del ciudadano no cuentan: debe haber una acción registrada por quien atiende el caso."""
        return self.seguimientos.filter(tipo=Seguimiento.Tipo.SEGUIMIENTO).exists()

    def motivo_descarte(self):
        if self.estado != self.Estado.DESCARTADO:
            return ""
        cambio = self.historial.filter(estado_nuevo=self.Estado.DESCARTADO).first()
        return cambio.observacion if cambio else ""

    def puede_cambiar_a(self, nuevo_estado):
        return nuevo_estado in self.TRANSICIONES[self.estado]

    def estados_siguientes(self):
        return [estado for estado in self.Estado if self.puede_cambiar_a(estado)]

    def bloquear_y_leer_estado(self):
        """Bloquea la fila del reporte hasta que termine la transacción y lee su estado real.

        Cambiar el estado, tomar el caso y asignarlo pasan por aquí: si dos personas lo hacen al mismo
        tiempo, SQL Server hace esperar a la segunda hasta que la primera termine.
        """
        self.estado = type(self).objects.select_for_update().values_list("estado", flat=True).get(pk=self.pk)

    def cambiar_estado(self, nuevo_estado, usuario, observacion="", estado_visto=None):
        """RF09: valida la transición y deja constancia en HistorialEstado.

        estado_visto es el estado que tenía el reporte en la página de quien hace el cambio. Si otra
        persona lo cambió mientras tanto, se rechaza: se queda el cambio que se guardó primero.
        """
        if not self.puede_gestionar(usuario):
            raise PermissionDenied("Este usuario no puede cambiar el estado de este reporte.")

        with transaction.atomic():
            # Si dos personas lo cambian al mismo tiempo, la segunda espera y trabaja con el estado ya actualizado.
            self.bloquear_y_leer_estado()
            if not self.puede_gestionar(usuario):
                # El administrador lo reasignó a otra institución mientras esta persona lo revisaba.
                raise ValidationError(self.motivo_no_gestiona(), code="reporte_desactualizado")
            if estado_visto and estado_visto != self.estado:
                raise ValidationError(
                    "No se pudo cambiar el estado: otro usuario ya lo cambió a "
                    f"«{self.get_estado_display()}» mientras lo revisabas. Revisa el estado actual.",
                    code="reporte_desactualizado",
                )
            if not self.puede_cambiar_a(nuevo_estado):
                raise ValidationError(
                    f"No se permite pasar de {self.get_estado_display()} a {self.Estado(nuevo_estado).label}."
                )
            if nuevo_estado == self.Estado.RESUELTO and not self.tiene_seguimiento_registrado():
                raise ValidationError("Registre al menos un seguimiento antes de marcar el reporte como resuelto.")
            if nuevo_estado == self.Estado.DESCARTADO and not observacion.strip():
                raise ValidationError("Indique el motivo por el que se descarta el reporte.")

            anterior = self.estado
            self.estado = nuevo_estado
            self._cambio_estado_autorizado = True
            try:
                self.save(update_fields=["estado", "fecha_actualizacion"])
            finally:
                self._cambio_estado_autorizado = False
            self.historial.create(
                usuario=usuario, estado_anterior=anterior, estado_nuevo=nuevo_estado, observacion=observacion
            )

    def marcar_como_resuelto(self, usuario, observacion=""):
        self.cambiar_estado(self.Estado.RESUELTO, usuario, observacion)

    def registrar_seguimiento(self, usuario, accion, descripcion):
        """RF10."""
        if not self.puede_gestionar(usuario):
            raise PermissionDenied("Este usuario no puede registrar seguimientos en este reporte.")
        return self.seguimientos.create(
            usuario=usuario, tipo=Seguimiento.Tipo.SEGUIMIENTO, accion=accion, descripcion=descripcion
        )

    def aportar_informacion(self, usuario, descripcion):
        """El dueño agrega información sin alterar lo que reportó originalmente."""
        if not self.puede_aportar_informacion(usuario):
            raise PermissionDenied("Solo el autor del reporte puede agregar información mientras el caso está abierto.")
        return self.seguimientos.create(
            usuario=usuario,
            tipo=Seguimiento.Tipo.APORTE_CIUDADANO,
            accion="Información adicional",
            descripcion=descripcion,
        )

    def evidencias_restantes(self, usuario):
        """Cuántas fotografías más puede subir este usuario (contando la inicial).

        El límite depende del rol: 5 para el ciudadano y el administrador, 10 para el responsable.
        """
        return max(usuario.maximo_evidencias() - self.evidencias.count(), 0)

    def agregar_evidencia(self, usuario, imagen, descripcion=""):
        """RF05. Se pueden seguir subiendo fotos del progreso hasta llegar al máximo del rol."""
        if not self.puede_agregar_evidencia(usuario):
            raise PermissionDenied("Este usuario no puede agregar evidencias a este reporte.")
        with transaction.atomic():
            # Bloquea el reporte hasta terminar: si dos personas suben fotos al mismo tiempo,
            # la segunda espera y cuenta ya con la foto de la primera, así nunca se pasa del límite.
            type(self).objects.select_for_update().filter(pk=self.pk).exists()
            if not self.evidencias_restantes(usuario):
                raise ValidationError(
                    f"El reporte ya tiene el máximo de {usuario.maximo_evidencias()} fotografías permitidas."
                )
            return self.evidencias.create(imagen=imagen, descripcion=descripcion)

    def asignar_a(self, institucion, usuario, observacion=""):
        """El administrador asigna (o reasigna) el reporte a una institución; desactiva la asignación anterior."""
        if not usuario.puede("asignar_reporte"):
            raise PermissionDenied("Solo el administrador puede asignar o reasignar reportes.")
        with transaction.atomic():
            self.bloquear_y_leer_estado()
            if not self.esta_activo():
                raise ValidationError("Solo se pueden asignar reportes pendientes o en proceso.")
            self.asignaciones.filter(activa=True).update(activa=False)
            return self.asignaciones.create(institucion=institucion, asignado_por=usuario, observacion=observacion)

    def tomar(self, usuario, observacion=""):
        """El responsable toma el caso para su institución. Si dos lo intentan a la vez, se queda el primero."""
        if not (usuario.is_authenticated and usuario.puede("tomar_reporte") and usuario.institucion_id):
            raise PermissionDenied("Solo un responsable con institución puede tomar casos.")
        with transaction.atomic():
            self.bloquear_y_leer_estado()
            actual = self.asignacion_activa()
            if actual and actual.institucion_id == usuario.institucion_id:
                raise ValidationError("Este caso ya está asignado a tu institución.", code="reporte_desactualizado")
            if actual:
                raise ValidationError(
                    f"No se pudo tomar el caso: ya lo atiende {actual.institucion}.", code="reporte_desactualizado"
                )
            if not self.esta_activo():
                raise ValidationError(
                    "No se pudo tomar el caso: ya está cerrado (resuelto o descartado).", code="reporte_desactualizado"
                )
            if not usuario.institucion.activa:
                raise ValidationError("Tu institución está inactiva; no puede tomar casos nuevos.")
            return self.asignaciones.create(
                institucion_id=usuario.institucion_id, asignado_por=usuario, observacion=observacion
            )

    def es_critico(self):
        return self.nivel_gravedad == self.NivelGravedad.ALTO and self.esta_activo()

    def asignacion_activa(self):
        return self.asignaciones.filter(activa=True).select_related("institucion").first()


class Evidencia(ModeloBase):
    """Entidad 8. Composición: se elimina junto con su reporte."""

    reporte = models.ForeignKey(ReporteAmbiental, on_delete=models.CASCADE, related_name="evidencias")
    imagen = models.ImageField(upload_to="evidencias/%Y/%m/")
    descripcion = models.CharField(
        "descripción",
        max_length=300,
        blank=True,
        db_default="",
        validators=[validador_texto(MINIMO_DESCRIPCION_FOTO)],
    )

    class Meta:
        verbose_name_plural = "evidencias"
        ordering = ["fecha_creacion"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(imagen=""),
                name="ck_evidencia_imagen_requerida",
                violation_error_message="La evidencia debe tener una fotografía.",
            ),
            models.CheckConstraint(
                condition=q_texto_libre_opcional("descripcion", MINIMO_DESCRIPCION_FOTO),
                name="ck_evidencia_descripcion_valida",
                violation_error_message=(
                    "La descripción de la fotografía debe incluir letras y no llevar símbolos raros."
                ),
            ),
        ]

    def __str__(self):
        return self.nombre_archivo

    @property
    def nombre_archivo(self):
        return os.path.basename(self.imagen.name)

    def delete(self, *args, **kwargs):
        self.imagen.delete(save=False)
        return super().delete(*args, **kwargs)


class Seguimiento(ModeloBase):
    """Entidad 9. Composición: se elimina junto con su reporte.

    Guarda tanto las acciones de quien atiende el caso como los aportes del ciudadano que lo reportó.
    """

    Tipo = TipoSeguimiento

    reporte = models.ForeignKey(ReporteAmbiental, on_delete=models.CASCADE, related_name="seguimientos")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="seguimientos")
    tipo = models.CharField(
        max_length=20, choices=Tipo.choices, default=Tipo.SEGUIMIENTO, db_default=Tipo.SEGUIMIENTO
    )
    accion = models.CharField("acción", max_length=100, validators=[validador_texto(MINIMO_ACCION_SEGUIMIENTO)])
    descripcion = models.CharField(
        "descripción", max_length=500, validators=[validador_texto(MINIMO_DESCRIPCION_SEGUIMIENTO)]
    )

    class Meta:
        ordering = ["-fecha_creacion"]
        constraints = [
            models.CheckConstraint(
                condition=q_valor_en("tipo", TipoSeguimiento.choices),
                name="ck_seguimiento_tipo_valido",
                violation_error_message="El tipo de seguimiento no es válido.",
            ),
            models.CheckConstraint(
                condition=q_texto_libre("accion", MINIMO_ACCION_SEGUIMIENTO),
                name="ck_seguimiento_accion_valida",
                violation_error_message="La acción debe incluir letras y no llevar símbolos raros.",
            ),
            models.CheckConstraint(
                condition=q_texto_libre("descripcion", MINIMO_DESCRIPCION_SEGUIMIENTO),
                name="ck_seguimiento_descripcion_valida",
                violation_error_message=(
                    f"La descripción debe tener al menos {MINIMO_DESCRIPCION_SEGUIMIENTO[0]} caracteres, "
                    "incluir letras y no llevar símbolos raros."
                ),
            ),
        ]

    def __str__(self):
        return f"{self.accion} — {self.reporte}"

    @property
    def es_aporte_ciudadano(self):
        return self.tipo == self.Tipo.APORTE_CIUDADANO


class HistorialEstado(ModeloBase):
    """Entidad 10. Solo la crea ReporteAmbiental.cambiar_estado()."""

    reporte = models.ForeignKey(ReporteAmbiental, on_delete=models.CASCADE, related_name="historial")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cambios_de_estado"
    )
    estado_anterior = models.CharField(max_length=20, choices=ReporteAmbiental.Estado.choices)
    estado_nuevo = models.CharField(max_length=20, choices=ReporteAmbiental.Estado.choices)
    observacion = models.CharField(
        "observación",
        max_length=300,
        blank=True,
        db_default="",
        validators=[validador_texto(MINIMO_OBSERVACION)],
    )

    class Meta:
        verbose_name = "historial de estado"
        verbose_name_plural = "historial de estados"
        ordering = ["-fecha_creacion"]
        constraints = [
            # Solo las transiciones de ReporteAmbiental.TRANSICIONES; implica que ambos estados son válidos.
            models.CheckConstraint(
                condition=reduce(or_, (
                    Q(estado_anterior=anterior, estado_nuevo__in=sorted(siguientes))
                    for anterior, siguientes in ReporteAmbiental.TRANSICIONES.items()
                )),
                name="ck_historial_transicion_valida",
                violation_error_message="Ese cambio de estado no está permitido.",
            ),
            models.CheckConstraint(
                condition=~Q(estado_nuevo=EstadoReporte.DESCARTADO) | q_contiene_letras("observacion"),
                name="ck_historial_motivo_descarte",
                violation_error_message="Indique el motivo por el que se descarta el reporte.",
            ),
            models.CheckConstraint(
                condition=q_texto_libre_opcional("observacion", MINIMO_OBSERVACION),
                name="ck_historial_observacion_valida",
                violation_error_message=(
                    f"La observación debe tener al menos {MINIMO_OBSERVACION[0]} caracteres, "
                    "incluir letras y no llevar símbolos raros."
                ),
            ),
        ]

    def __str__(self):
        return f"{self.reporte}: {self.get_estado_anterior_display()} → {self.get_estado_nuevo_display()}"
