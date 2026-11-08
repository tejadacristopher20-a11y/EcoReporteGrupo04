from django.contrib import admin

from Eco_Reporte_Comunitario.admin_base import ModeloAdmin

from .models import Comunidad, Departamento, Distrito, Ubicacion


@admin.register(Departamento)
class DepartamentoAdmin(ModeloAdmin):
    search_fields = ("nombre",)


@admin.register(Distrito)
class DistritoAdmin(ModeloAdmin):
    list_display = ("nombre", "departamento")
    list_filter = ("departamento",)
    search_fields = ("nombre",)


@admin.register(Comunidad)
class ComunidadAdmin(ModeloAdmin):
    nombre_femenino = True
    list_display = ("nombre", "distrito")
    list_filter = ("distrito__departamento",)
    search_fields = ("nombre",)


@admin.register(Ubicacion)
class UbicacionAdmin(ModeloAdmin):
    nombre_femenino = True
    list_display = ("referencia", "comunidad", "latitud", "longitud")
    list_filter = ("comunidad",)
    search_fields = ("referencia", "direccion")
