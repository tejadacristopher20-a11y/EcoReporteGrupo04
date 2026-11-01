from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from Eco_Reporte_Comunitario.modelos_base import ModeloBase
from Eco_Reporte_Comunitario.restricciones import (
    MINIMO_REFERENCIA,
    q_nombre_general,
    q_texto_libre,
    q_texto_libre_opcional,
    validador_texto,
    validar_nombre_general,
)


class Departamento(ModeloBase):
    """Entidad 2."""

    nombre = models.CharField(max_length=50, unique=True, validators=[validar_nombre_general])

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.CheckConstraint(
                condition=q_nombre_general("nombre"),
                name="ck_departamento_nombre_valido",
                violation_error_message="El nombre del departamento solo admite letras, números y signos básicos.",
            ),
        ]

    def __str__(self):
        return self.nombre


class Distrito(ModeloBase):
    """Entidad 3."""

    nombre = models.CharField(max_length=100, validators=[validar_nombre_general])
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, related_name="distritos")

    class Meta:
        ordering = ["departamento__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["nombre", "departamento"], name="distrito_unico_por_departamento"),
            models.CheckConstraint(
                condition=q_nombre_general("nombre"),
                name="ck_distrito_nombre_valido",
                violation_error_message="El nombre del distrito solo admite letras, números y signos básicos.",
            ),
        ]

    def __str__(self):
        return f"{self.nombre}, {self.departamento}"


class Comunidad(ModeloBase):
    """Entidad 4."""

    nombre = models.CharField(max_length=100, validators=[validar_nombre_general])
    distrito = models.ForeignKey(Distrito, on_delete=models.PROTECT, related_name="comunidades")

    class Meta:
        verbose_name_plural = "comunidades"
        ordering = ["distrito__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["nombre", "distrito"], name="comunidad_unica_por_distrito"),
            models.CheckConstraint(
                condition=q_nombre_general("nombre"),
                name="ck_comunidad_nombre_valido",
                violation_error_message="El nombre de la comunidad solo admite letras, números y signos básicos.",
            ),
        ]

    def __str__(self):
        return f"{self.nombre}, {self.distrito}"


class Ubicacion(ModeloBase):
    """Entidad 5."""

    comunidad = models.ForeignKey(Comunidad, on_delete=models.PROTECT, related_name="ubicaciones")
    referencia = models.CharField(max_length=200, validators=[validador_texto(MINIMO_REFERENCIA)])
    direccion = models.CharField(
        "dirección", max_length=250, blank=True, db_default="", validators=[validador_texto(MINIMO_REFERENCIA)]
    )
    latitud = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitud = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    class Meta:
        verbose_name = "ubicación"
        verbose_name_plural = "ubicaciones"
        constraints = [
            models.CheckConstraint(
                condition=q_texto_libre("referencia", MINIMO_REFERENCIA),
                name="ck_ubicacion_referencia_valida",
                violation_error_message=(
                    f"La referencia debe tener al menos {MINIMO_REFERENCIA[0]} caracteres y describir "
                    "el lugar con letras, sin símbolos raros."
                ),
            ),
            models.CheckConstraint(
                condition=q_texto_libre_opcional("direccion", MINIMO_REFERENCIA),
                name="ck_ubicacion_direccion_valida",
                violation_error_message=(
                    f"La dirección debe tener al menos {MINIMO_REFERENCIA[0]} caracteres, incluir letras "
                    "y no llevar símbolos raros."
                ),
            ),
            models.CheckConstraint(
                condition=Q(latitud__isnull=True) | Q(latitud__gte=-90, latitud__lte=90),
                name="ck_ubicacion_latitud_rango",
                violation_error_message="La latitud debe estar entre -90 y 90.",
            ),
            models.CheckConstraint(
                condition=Q(longitud__isnull=True) | Q(longitud__gte=-180, longitud__lte=180),
                name="ck_ubicacion_longitud_rango",
                violation_error_message="La longitud debe estar entre -180 y 180.",
            ),
            models.CheckConstraint(
                condition=Q(latitud__isnull=True, longitud__isnull=True)
                | Q(latitud__isnull=False, longitud__isnull=False),
                name="ck_ubicacion_coordenadas_completas",
                violation_error_message="Ingrese latitud y longitud juntas, o ninguna de las dos.",
            ),
        ]

    def __str__(self):
        return f"{self.referencia} ({self.comunidad.nombre})"

    @property
    def tiene_coordenadas(self):
        return self.latitud is not None and self.longitud is not None
