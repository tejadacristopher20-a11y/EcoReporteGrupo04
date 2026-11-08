from django.contrib import admin, messages
from django.contrib.admin.models import DELETION, LogEntry
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.utils import unquote
from django.shortcuts import redirect


class AvisoEliminadoAdminMixin:
    """Cuando se abre un registro que ya fue borrado (al volver «Atrás» o por un doble clic en
    «Sí, estoy seguro»), Django avisa «usuario con el ID “7” no existe. ¿Quizás fue eliminado?».

    Aquí se cambia por «El usuario «Ana López» fue eliminado.», con el nombre que guardó el historial
    del panel (LogEntry) al borrarlo, y se vuelve a la lista de ese modelo en lugar del inicio del panel.
    """

    # Para el artículo y la terminación: «La comunidad … fue eliminada» / «El usuario … fue eliminado».
    nombre_femenino = False

    def _get_obj_does_not_exist_redirect(self, request, opts, object_id):
        borrado = (
            LogEntry.objects.filter(
                content_type=get_content_type_for_model(self.model),
                object_id=unquote(object_id),
                action_flag=DELETION,
            )
            .order_by("-action_time")
            .first()
        )
        if borrado is None:
            # Nunca existió (dirección mal escrita): se deja el aviso original de Django.
            return super()._get_obj_does_not_exist_redirect(request, opts, object_id)
        articulo, terminacion = ("La", "a") if self.nombre_femenino else ("El", "o")
        self.message_user(
            request,
            f"{articulo} {opts.verbose_name} «{borrado.object_repr}» fue eliminad{terminacion}.",
            messages.INFO,
        )
        return redirect(f"admin:{opts.app_label}_{opts.model_name}_changelist")


class ModeloAdmin(AvisoEliminadoAdminMixin, admin.ModelAdmin):
    """ModelAdmin del proyecto: igual al de Django, con el aviso de registro eliminado."""
