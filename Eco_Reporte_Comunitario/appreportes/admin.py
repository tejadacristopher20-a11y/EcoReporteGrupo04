from django.contrib import admin

from Eco_Reporte_Comunitario.admin_base import ModeloAdmin

from .forms import EvidenciaAdminForm
from .models import CategoriaProblema, Evidencia, HistorialEstado, ReporteAmbiental, Seguimiento

# Sin borrado en bloque en todo el panel: la confirmación de esa acción es la respuesta a un formulario
# (POST) y, al volver con «Atrás», el navegador pide reenviarlo. Se elimina desde la ficha de cada
# registro (botón «Eliminar»), que sí redirige después de confirmar.
admin.site.disable_action("delete_selected")


@admin.register(CategoriaProblema)
class CategoriaProblemaAdmin(ModeloAdmin):
    nombre_femenino = True
    list_display = ("nombre", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre",)


class EvidenciaInline(admin.TabularInline):
    model = Evidencia
    form = EvidenciaAdminForm  # Convierte a WebP y valida los 5 MB, igual que la web.
    extra = 0

    def get_max_num(self, request, obj=None, **kwargs):
        # El mismo límite de fotografías que tiene en la web el rol de quien está conectado.
        return request.user.maximo_evidencias()


class SeguimientoInline(admin.TabularInline):
    model = Seguimiento
    extra = 0
    fields = ("tipo", "accion", "descripcion", "usuario")


class HistorialEstadoInline(admin.TabularInline):
    """Solo lectura: el historial lo genera cambiar_estado()."""

    model = HistorialEstado
    extra = 0
    can_delete = False
    readonly_fields = ("estado_anterior", "estado_nuevo", "usuario", "observacion", "fecha_creacion")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ReporteAmbiental)
class ReporteAmbientalAdmin(ModeloAdmin):
    list_display = ("titulo", "categoria", "nivel_gravedad", "estado", "usuario", "fecha_incidente")
    list_filter = ("estado", "nivel_gravedad", "categoria", "ubicacion__comunidad")
    search_fields = ("titulo", "descripcion")
    readonly_fields = ("estado",)
    inlines = [EvidenciaInline, SeguimientoInline, HistorialEstadoInline]


@admin.register(Seguimiento)
class SeguimientoAdmin(ModeloAdmin):
    list_display = ("reporte", "tipo", "accion", "usuario", "fecha_creacion")
    list_filter = ("tipo",)
    search_fields = ("accion", "descripcion", "reporte__titulo")
