from django.contrib import admin

from Eco_Reporte_Comunitario.admin_base import ModeloAdmin

from .models import AsignacionReporte, Institucion


@admin.register(Institucion)
class InstitucionAdmin(ModeloAdmin):
    nombre_femenino = True
    list_display = ("nombre", "tipo", "distrito", "activa")
    list_filter = ("tipo", "activa")
    search_fields = ("nombre",)


@admin.register(AsignacionReporte)
class AsignacionReporteAdmin(ModeloAdmin):
    nombre_femenino = True
    list_display = ("reporte", "institucion", "asignado_por", "activa", "fecha_creacion")
    list_filter = ("activa", "institucion")