from django.conf import settings
from django.db import models
from django.db.models import Q

from Eco_Reporte_Comunitario.modelos_base import ModeloBase
from Eco_Reporte_Comunitario.restricciones import (
    MINIMO_OBSERVACION,
    q_correo,
    q_nombre_general,
    q_telefono_opcional,
    q_texto_libre_opcional,
    q_valor_en,
    validador_texto,
    validar_nombre_general,
    validar_telefono,
)


class TipoInstitucion(models.TextChoices):
    ALCALDIA = "ALCALDIA", "Alcaldía"
    GOBIERNO = "GOBIERNO", "Institución de gobierno"
    ONG = "ONG", "Organización ambiental (ONG)"
    CENTRO_EDUCATIVO = "CENTRO_EDUCATIVO", "Centro educativo"
    OTRA = "OTRA", "Otra"


class Institucion(ModeloBase):
    """Entidad 11. Alcaldías, MARN, ONG o centros educativos que atienden los casos."""

    Tipo = TipoInstitucion

    nombre = models.CharField(max_length=150, unique=True, validators=[validar_nombre_general])
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    telefono = models.CharField(
        "teléfono", max_length=15, blank=True, db_default="", validators=[validar_telefono]
    )
    correo = models.EmailField(blank=True, db_default="")
    distrito = models.ForeignKey(
        "appterritorio.Distrito",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instituciones",
    )
    activa = models.BooleanField(default=True, db_default=True)

    class Meta:
        verbose_name = "institución"
        verbose_name_plural = "instituciones"
        ordering = ["nombre"]
        constraints = [
            models.CheckConstraint(
                condition=q_nombre_general("nombre"),
                name="ck_institucion_nombre_valido",
                violation_error_message="El nombre de la institución solo admite letras, números y signos básicos.",
            ),
            models.CheckConstraint(
                condition=q_valor_en("tipo", TipoInstitucion.choices),
                name="ck_institucion_tipo_valido",
                violation_error_message="El tipo de institución no es válido.",
            ),
            models.CheckConstraint(
                condition=q_telefono_opcional("telefono"),
                name="ck_institucion_telefono_valido",
                violation_error_message="El teléfono debe tener 8 números y, como máximo, un guion medio (ej. 2300-0000).",
            ),
            models.CheckConstraint(
                condition=Q(correo="") | q_correo("correo"),
                name="ck_institucion_correo_valido",
                violation_error_message="El correo de la institución no es válido.",
            ),
        ]

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
    activa = models.BooleanField(default=True, db_default=True)
    observacion = models.CharField(
        "observación",
        max_length=300,
        blank=True,
        db_default="",
        validators=[validador_texto(MINIMO_OBSERVACION)],
    )

    class Meta:
        verbose_name = "asignación de reporte"
        verbose_name_plural = "asignaciones de reportes"
        ordering = ["-fecha_creacion"]
        constraints = [
            models.UniqueConstraint(
                fields=["reporte"],
                condition=Q(activa=True),
                name="uq_asignacion_una_activa_por_reporte",
                violation_error_message="El reporte ya tiene una asignación activa.",
            ),
            models.CheckConstraint(
                condition=q_texto_libre_opcional("observacion", MINIMO_OBSERVACION),
                name="ck_asignacion_observacion_valida",
                violation_error_message=(
                    f"La observación debe tener al menos {MINIMO_OBSERVACION[0]} caracteres, "
                    "incluir letras y no llevar símbolos raros."
                ),
            ),
        ]

    def __str__(self):
        return f"{self.reporte} → {self.institucion}"
