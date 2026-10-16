from django.db import models


class ModeloBase(models.Model):
    """Clase abstracta: no crea tabla, solo hereda sus campos a las demás entidades."""

    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("fecha de actualización", auto_now=True)

    class Meta:
        abstract = True
