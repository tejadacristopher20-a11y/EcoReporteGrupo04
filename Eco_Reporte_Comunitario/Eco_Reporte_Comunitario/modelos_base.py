from django.db import models
from django.db.models.functions import Now


class ModeloBase(models.Model):
    """Clase abstracta: no crea tabla, solo hereda sus campos a las demás entidades.

    db_default crea el DEFAULT en SQL Server, para que un INSERT hecho directamente
    con SQL también registre las fechas.
    """

    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True, db_default=Now())
    fecha_actualizacion = models.DateTimeField("fecha de actualización", auto_now=True, db_default=Now())

    class Meta:
        abstract = True
