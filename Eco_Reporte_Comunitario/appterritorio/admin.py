from django.contrib import admin

from .models import Comunidad, Departamento, Distrito, Ubicacion


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)


@admin.register(Distrito)
class DistritoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "departamento")
    list_filter = ("departamento",)
    search_fields = ("nombre",)


@admin.register(Comunidad)
class ComunidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "distrito")
    list_filter = ("distrito__departamento",)
    search_fields = ("nombre",)


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ("referencia", "comunidad", "latitud", "longitud")
    list_filter = ("comunidad",)
    search_fields = ("referencia", "direccion")
