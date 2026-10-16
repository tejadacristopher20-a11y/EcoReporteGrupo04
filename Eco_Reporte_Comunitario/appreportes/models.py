import os

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from Eco_Reporte_Comunitario.modelos_base import ModeloBase


class CategoriaProblema(ModeloBase):
    """Entidad 6."""

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField("descripción", max_length=250)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "categoría de problema"
        verbose_name_plural = "categorías de problema"
        ordering = ["nombre"]

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

    def criticos(self):
        return self.filter(nivel_gravedad=ReporteAmbiental.NivelGravedad.ALTO).exclude(
            estado=ReporteAmbiental.Estado.RESUELTO
        )


class ReporteAmbiental(ModeloBase):
    """Entidad 7. El estado solo puede cambiarse con cambiar_estado()."""

    class NivelGravedad(models.TextChoices):
        BAJO = "BAJO", "Bajo"
        MEDIO = "MEDIO", "Medio"
        ALTO = "ALTO", "Alto"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        RESUELTO = "RESUELTO", "Resuelto"

    # Transiciones permitidas. RESUELTO → EN_PROCESO permite reabrir un caso.
    TRANSICIONES = {
        Estado.PENDIENTE: {Estado.EN_PROCESO},
        Estado.EN_PROCESO: {Estado.RESUELTO},
        Estado.RESUELTO: {Estado.EN_PROCESO},
    }

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reportes")
    categoria = models.ForeignKey(
        CategoriaProblema, on_delete=models.PROTECT, related_name="reportes", verbose_name="categoría"
    )
    ubicacion = models.ForeignKey(
        "appterritorio.Ubicacion", on_delete=models.PROTECT, related_name="reportes", verbose_name="ubicación"
    )
    titulo = models.CharField("título", max_length=150)
    descripcion = models.CharField("descripción", max_length=1000)
    fecha_incidente = models.DateField("fecha del incidente")
    nivel_gravedad = models.CharField(max_length=10, choices=NivelGravedad.choices)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE, editable=False)

    objects = ReporteQuerySet.as_manager()

    _cambio_estado_autorizado = False

    class Meta:
        verbose_name = "reporte ambiental"
        verbose_name_plural = "reportes ambientales"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("appreportes:detalle", args=[self.pk])

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

    def clean(self):
        super().clean()
        if self.fecha_incidente and self.fecha_incidente > timezone.localdate():
            raise ValidationError({"fecha_incidente": "La fecha del incidente no puede ser futura."})

    # --- Reglas de acceso: cada vista pregunta al reporte qué puede hacer el usuario ---

    def es_propietario(self, usuario):
        return usuario.is_authenticated and self.usuario_id == usuario.pk

    def puede_modificar(self, usuario):
        """El ciudadano solo edita sus reportes mientras siguen pendientes."""
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
        if not usuario.is_authenticated:
            return False
        if usuario.puede("eliminar_cualquier_reporte"):
            return True
        return (
            self.es_propietario(usuario)
            and usuario.puede("eliminar_reporte_propio")
            and self.estado == self.Estado.PENDIENTE
        )

    def puede_gestionar(self, usuario):
        """Cambiar estado y registrar seguimiento: el administrador, o el responsable de la institución asignada."""
        if not usuario.is_authenticated or not usuario.puede("cambiar_estado"):
            return False
        if usuario.puede("asignar_reporte"):
            return True
        asignacion = self.asignacion_activa()
        return asignacion is not None and asignacion.institucion_id == usuario.institucion_id

    def puede_agregar_evidencia(self, usuario):
        return self.puede_modificar(usuario) or self.puede_gestionar(usuario)

    def puede_cambiar_a(self, nuevo_estado):
        return nuevo_estado in self.TRANSICIONES[self.estado]

    def estados_siguientes(self):
        return [estado for estado in self.Estado if self.puede_cambiar_a(estado)]

    def cambiar_estado(self, nuevo_estado, usuario, observacion=""):
        """RF09: valida la transición y deja constancia en HistorialEstado."""
        if not self.puede_gestionar(usuario):
            raise PermissionDenied("Este usuario no puede cambiar el estado de este reporte.")
        if not self.puede_cambiar_a(nuevo_estado):
            raise ValidationError(
                f"No se permite pasar de {self.get_estado_display()} a {self.Estado(nuevo_estado).label}."
            )
        if nuevo_estado == self.Estado.RESUELTO and not self.seguimientos.exists():
            raise ValidationError("Registre al menos un seguimiento antes de marcar el reporte como resuelto.")

        with transaction.atomic():
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
        return self.seguimientos.create(usuario=usuario, accion=accion, descripcion=descripcion)

    def agregar_evidencia(self, usuario, imagen, descripcion=""):
        """RF05."""
        if not self.puede_agregar_evidencia(usuario):
            raise PermissionDenied("Este usuario no puede agregar evidencias a este reporte.")
        return self.evidencias.create(imagen=imagen, descripcion=descripcion)

    def asignar_a(self, institucion, usuario, observacion=""):
        """Asigna el reporte a una institución; desactiva la asignación anterior."""
        if not usuario.puede("asignar_reporte"):
            raise PermissionDenied("Solo un administrador puede asignar reportes.")
        with transaction.atomic():
            self.asignaciones.filter(activa=True).update(activa=False)
            return self.asignaciones.create(institucion=institucion, asignado_por=usuario, observacion=observacion)

    def es_critico(self):
        return self.nivel_gravedad == self.NivelGravedad.ALTO and self.estado != self.Estado.RESUELTO

    def asignacion_activa(self):
        return self.asignaciones.filter(activa=True).select_related("institucion").first()


class Evidencia(ModeloBase):
    """Entidad 8. Composición: se elimina junto con su reporte."""

    reporte = models.ForeignKey(ReporteAmbiental, on_delete=models.CASCADE, related_name="evidencias")
    imagen = models.ImageField(upload_to="evidencias/%Y/%m/")
    descripcion = models.CharField("descripción", max_length=300, blank=True)

    class Meta:
        verbose_name_plural = "evidencias"
        ordering = ["fecha_creacion"]

    def __str__(self):
        return self.nombre_archivo

    @property
    def nombre_archivo(self):
        return os.path.basename(self.imagen.name)

    def delete(self, *args, **kwargs):
        self.imagen.delete(save=False)
        return super().delete(*args, **kwargs)


class Seguimiento(ModeloBase):
    """Entidad 9. Composición: se elimina junto con su reporte."""

    reporte = models.ForeignKey(ReporteAmbiental, on_delete=models.CASCADE, related_name="seguimientos")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="seguimientos")
    accion = models.CharField("acción", max_length=100)
    descripcion = models.CharField("descripción", max_length=500)

    class Meta:
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.accion} — {self.reporte}"


class HistorialEstado(ModeloBase):
    """Entidad 10. Solo la crea ReporteAmbiental.cambiar_estado()."""

    reporte = models.ForeignKey(ReporteAmbiental, on_delete=models.CASCADE, related_name="historial")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cambios_de_estado"
    )
    estado_anterior = models.CharField(max_length=20, choices=ReporteAmbiental.Estado.choices)
    estado_nuevo = models.CharField(max_length=20, choices=ReporteAmbiental.Estado.choices)
    observacion = models.CharField("observación", max_length=300, blank=True)

    class Meta:
        verbose_name = "historial de estado"
        verbose_name_plural = "historial de estados"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.reporte}: {self.get_estado_anterior_display()} → {self.get_estado_nuevo_display()}"
