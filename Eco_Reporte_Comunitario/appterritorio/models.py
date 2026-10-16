from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from Eco_Reporte_Comunitario.modelos_base import ModeloBase


class Departamento(ModeloBase):
    """Entidad 2."""

    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Distrito(ModeloBase):
    """Entidad 3."""

    nombre = models.CharField(max_length=100)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, related_name="distritos")

    class Meta:
        ordering = ["departamento__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["nombre", "departamento"], name="distrito_unico_por_departamento"),
        ]

    def __str__(self):
        return f"{self.nombre}, {self.departamento}"


class Comunidad(ModeloBase):
    """Entidad 4."""

    nombre = models.CharField(max_length=100)
    distrito = models.ForeignKey(Distrito, on_delete=models.PROTECT, related_name="comunidades")

    class Meta:
        verbose_name_plural = "comunidades"
        ordering = ["distrito__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["nombre", "distrito"], name="comunidad_unica_por_distrito"),
        ]

    def __str__(self):
        return f"{self.nombre}, {self.distrito}"


class Ubicacion(ModeloBase):
    """Entidad 5."""

    comunidad = models.ForeignKey(Comunidad, on_delete=models.PROTECT, related_name="ubicaciones")
    referencia = models.CharField(max_length=200)
    direccion = models.CharField("dirección", max_length=250, blank=True)
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

    def __str__(self):
        return f"{self.referencia} ({self.comunidad.nombre})"

    def clean(self):
        super().clean()
        if (self.latitud is None) != (self.longitud is None):
            raise ValidationError("Ingrese latitud y longitud juntas, o ninguna de las dos.")

    @property
    def tiene_coordenadas(self):
        return self.latitud is not None and self.longitud is not None
