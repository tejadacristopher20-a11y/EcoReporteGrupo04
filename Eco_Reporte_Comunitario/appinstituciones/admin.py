from django.contrib import admin

from .models import AsignacionReporte, Institucion


@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "distrito", "activa")
    list_filter = ("tipo", "activa")
    search_fields = ("nombre",)


@admin.register(AsignacionReporte)
class AsignacionReporteAdmin(admin.ModelAdmin):
    list_display = ("reporte", "institucion", "asignado_por", "activa", "fecha_creacion")
    list_filter = ("activa", "institucion")
