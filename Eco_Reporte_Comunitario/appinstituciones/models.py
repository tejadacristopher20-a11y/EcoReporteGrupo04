from django.conf import settings
from django.db import models

from Eco_Reporte_Comunitario.modelos_base import ModeloBase


class Institucion(ModeloBase):
    """Entidad 11. Alcaldías, MARN, ONG o centros educativos que atienden los casos."""

    class Tipo(models.TextChoices):
        ALCALDIA = "ALCALDIA", "Alcaldía"
        GOBIERNO = "GOBIERNO", "Institución de gobierno"
        ONG = "ONG", "Organización ambiental (ONG)"
        CENTRO_EDUCATIVO = "CENTRO_EDUCATIVO", "Centro educativo"
        OTRA = "OTRA", "Otra"

    nombre = models.CharField(max_length=150, unique=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    telefono = models.CharField("teléfono", max_length=15, blank=True)
    correo = models.EmailField(blank=True)
    distrito = models.ForeignKey(
        "appterritorio.Distrito",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instituciones",
    )
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "institución"
        verbose_name_plural = "instituciones"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def reportes_asignados(self):
        from appreportes.models import ReporteAmbiental

        return ReporteAmbiental.objects.filter(asignaciones__institucion=self, asignaciones__activa=True)


class AsignacionReporte(ModeloBase):
    """Entidad 12. Se crea con ReporteAmbiental.asignar_a()."""

    reporte = models.ForeignKey(
        "appreportes.ReporteAmbiental", on_delete=models.CASCADE, related_name="asignaciones"
    )
    institucion = models.ForeignKey(
        Institucion, on_delete=models.PROTECT, related_name="asignaciones", verbose_name="institución"
    )
    asignado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="asignaciones_realizadas"
    )
    activa = models.BooleanField(default=True)
    observacion = models.CharField("observación", max_length=300, blank=True)

    class Meta:
        verbose_name = "asignación de reporte"
        verbose_name_plural = "asignaciones de reportes"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.reporte} → {self.institucion}"
