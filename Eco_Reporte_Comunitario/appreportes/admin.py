from django.contrib import admin

from .models import CategoriaProblema, Evidencia, HistorialEstado, ReporteAmbiental, Seguimiento


@admin.register(CategoriaProblema)
class CategoriaProblemaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre",)


class EvidenciaInline(admin.TabularInline):
    model = Evidencia
    extra = 0


class SeguimientoInline(admin.TabularInline):
    model = Seguimiento
    extra = 0


class HistorialEstadoInline(admin.TabularInline):
    """Solo lectura: el historial lo genera cambiar_estado()."""

    model = HistorialEstado
    extra = 0
    can_delete = False
    readonly_fields = ("estado_anterior", "estado_nuevo", "usuario", "observacion", "fecha_creacion")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ReporteAmbiental)
class ReporteAmbientalAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "nivel_gravedad", "estado", "usuario", "fecha_incidente")
    list_filter = ("estado", "nivel_gravedad", "categoria", "ubicacion__comunidad")
    search_fields = ("titulo", "descripcion")
    readonly_fields = ("estado",)
    inlines = [EvidenciaInline, SeguimientoInline, HistorialEstadoInline]
