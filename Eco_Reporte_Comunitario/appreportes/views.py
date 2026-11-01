from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from Eco_Reporte_Comunitario.restricciones import mensaje_restriccion_violada

from .forms import (
    AporteForm,
    AsignarForm,
    CambiarEstadoForm,
    EvidenciaForm,
    FiltroReportesForm,
    ReporteForm,
    SeguimientoForm,
)
from .models import CategoriaProblema, ReporteAmbiental

Estado = ReporteAmbiental.Estado


def reportes_con_relaciones():
    return ReporteAmbiental.objects.select_related("categoria", "ubicacion__comunidad").prefetch_related(
        "evidencias"
    )


class PermisoRequeridoMixin(LoginRequiredMixin):
    """Exige iniciar sesión y, además, que el rol del usuario tenga el permiso indicado."""

    permiso_requerido = None

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and self.permiso_requerido
            and not request.user.puede(self.permiso_requerido)
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ReporteExistenteMixin:
    """Si el reporte no existe (fue eliminado o la dirección es incorrecta), vuelve a la lista con un aviso
    en lugar de mostrar la página de error «No encontrado»."""

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Http404:
            messages.warning(request, "El reporte que buscas no existe o fue eliminado.")
            return redirect("appreportes:lista")


class GuardarReporteMixin:
    """Guarda el formulario del reporte; si SQL Server rechaza algún dato, muestra el motivo en el formulario."""

    mensaje_exito = ""

    def form_valid(self, form):
        try:
            self.object = form.guardar(self.request.user)
        except IntegrityError as error:
            form.add_error(None, mensaje_restriccion_violada(error))
            return self.form_invalid(form)
        messages.success(self.request, self.mensaje_exito)
        return redirect(self.object)


class FiltroReportesMixin:
    """Aplica el formulario de filtros (RF11) a cualquier lista de reportes."""

    paginate_by = 10
    context_object_name = "reportes"

    def get_reportes_base(self):
        raise NotImplementedError

    def get_queryset(self):
        self.filtro = FiltroReportesForm(self.request.GET or None)
        reportes = self.get_reportes_base()
        if self.filtro.is_valid():
            reportes = reportes.filtrar(**self.filtro.cleaned_data)
        return reportes

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["filtro"] = self.filtro
        return contexto


class InicioView(TemplateView):
    """Página pública: resumen de casos sin datos personales de quien reporta."""

    template_name = "appreportes/inicio.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["totales"] = ReporteAmbiental.objects.aggregate(
            total=Count("id"),
            pendientes=Count("id", filter=Q(estado=Estado.PENDIENTE)),
            en_proceso=Count("id", filter=Q(estado=Estado.EN_PROCESO)),
            resueltos=Count("id", filter=Q(estado=Estado.RESUELTO)),
            descartados=Count("id", filter=Q(estado=Estado.DESCARTADO)),
        )
        contexto["criticos"] = ReporteAmbiental.objects.criticos().count()
        contexto["ultimos_reportes"] = reportes_con_relaciones()[:5]
        contexto["categorias"] = CategoriaProblema.objects.filter(activa=True)
        return contexto


class ReporteListView(FiltroReportesMixin, ListView):
    """RF06: consulta pública de todos los reportes."""

    template_name = "appreportes/reporte_lista.html"
    extra_context = {"titulo_pagina": "Reportes de la comunidad"}

    def get_reportes_base(self):
        return reportes_con_relaciones()


class PanelView(LoginRequiredMixin, FiltroReportesMixin, ListView):
    """Cada rol ve sus reportes gracias al método polimórfico reportes_de_panel()."""

    template_name = "appreportes/reporte_lista.html"

    def get_reportes_base(self):
        ids = self.request.user.reportes_de_panel().values("pk")
        return reportes_con_relaciones().filter(pk__in=ids)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo_pagina"] = self.request.user.titulo_panel()
        contexto["es_panel"] = True
        return contexto


class ReporteDetailView(ReporteExistenteMixin, DetailView):
    template_name = "appreportes/reporte_detalle.html"
    context_object_name = "reporte"

    def get_queryset(self):
        return ReporteAmbiental.objects.select_related("categoria", "ubicacion__comunidad__distrito__departamento")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        reporte, usuario = self.object, self.request.user
        puede_gestionar = reporte.puede_gestionar(usuario)
        contexto.update(
            evidencias=reporte.evidencias.all(),
            seguimientos=reporte.seguimientos.select_related("usuario__institucion"),
            historial=reporte.historial.select_related("usuario__institucion"),
            asignacion=reporte.asignacion_activa(),
            motivo_descarte=reporte.motivo_descarte(),
            esta_activo=reporte.esta_activo(),
            tiene_seguimiento_registrado=reporte.tiene_seguimiento_registrado(),
            es_propietario=reporte.es_propietario(usuario),
            puede_modificar=reporte.puede_modificar(usuario),
            puede_eliminar=reporte.puede_eliminar(usuario),
            puede_gestionar=puede_gestionar,
        )
        if reporte.puede_agregar_evidencia(usuario):
            contexto["evidencia_form"] = EvidenciaForm()
        if reporte.puede_aportar_informacion(usuario):
            contexto["aporte_form"] = AporteForm()
        if puede_gestionar:
            contexto["seguimiento_form"] = SeguimientoForm()
            if reporte.estados_siguientes():
                contexto["estado_form"] = CambiarEstadoForm(reporte=reporte)
        if reporte.puede_asignar(usuario):
            contexto["asignar_form"] = AsignarForm()
        return contexto


class ReporteCreateView(PermisoRequeridoMixin, GuardarReporteMixin, CreateView):
    """RF02."""

    permiso_requerido = "crear_reporte"
    form_class = ReporteForm
    template_name = "appreportes/reporte_form.html"
    extra_context = {"titulo_pagina": "Nuevo reporte"}
    mensaje_exito = "Tu reporte fue registrado. ¡Gracias por cuidar tu comunidad!"


class ReporteUpdateView(ReporteExistenteMixin, LoginRequiredMixin, GuardarReporteMixin, UpdateView):
    """RF07."""

    model = ReporteAmbiental
    form_class = ReporteForm
    template_name = "appreportes/reporte_form.html"
    extra_context = {"titulo_pagina": "Editar reporte"}
    mensaje_exito = "El reporte fue actualizado."

    def get_object(self, queryset=None):
        reporte = super().get_object(queryset)
        if not reporte.puede_modificar(self.request.user):
            raise PermissionDenied
        return reporte


class ReporteDeleteView(ReporteExistenteMixin, LoginRequiredMixin, DeleteView):
    """RF08."""

    model = ReporteAmbiental
    template_name = "appreportes/reporte_confirmar_eliminar.html"
    context_object_name = "reporte"
    success_url = reverse_lazy("appreportes:panel")

    def get_object(self, queryset=None):
        reporte = super().get_object(queryset)
        if not reporte.puede_eliminar(self.request.user):
            raise PermissionDenied
        return reporte

    def form_valid(self, form):
        messages.success(self.request, f"El reporte «{self.object}» fue eliminado.")
        return super().form_valid(form)


class AccionSobreReporteView(ReporteExistenteMixin, LoginRequiredMixin, View):
    """Clase base (patrón plantilla) para las acciones que se envían desde el detalle del reporte.

    Si los datos no son válidos, vuelve a mostrar el detalle con los errores debajo de cada campo.
    """

    http_method_names = ["post"]
    form_class = None
    nombre_formulario = None  # Nombre con el que la plantilla del detalle muestra el formulario.
    mensaje_exito = ""

    def tiene_permiso(self, reporte, usuario):
        raise NotImplementedError

    def ejecutar(self, reporte, datos, usuario):
        raise NotImplementedError

    def get_form_kwargs(self, reporte):
        return {}

    def post(self, request, pk):
        reporte = get_object_or_404(ReporteAmbiental, pk=pk)
        if not self.tiene_permiso(reporte, request.user):
            raise PermissionDenied
        form = self.form_class(request.POST, request.FILES, **self.get_form_kwargs(reporte))
        if form.is_valid():
            try:
                with transaction.atomic():
                    self.ejecutar(reporte, form.cleaned_data, request.user)
            except ValidationError as error:
                form.add_error(None, error.messages)
            except IntegrityError as error:
                form.add_error(None, mensaje_restriccion_violada(error))
            else:
                messages.success(request, self.mensaje_exito)
                return redirect(reporte)
        return self.mostrar_detalle_con_errores(reporte, form)

    def mostrar_detalle_con_errores(self, reporte, form):
        messages.error(self.request, "No se pudo guardar. Revise los datos marcados en rojo en el formulario.")
        detalle = ReporteDetailView()
        detalle.setup(self.request, pk=reporte.pk)
        detalle.object = reporte
        contexto = detalle.get_context_data(object=reporte)
        contexto[self.nombre_formulario] = form
        return render(self.request, detalle.template_name, contexto)


class AgregarEvidenciaView(AccionSobreReporteView):
    """RF05."""

    form_class = EvidenciaForm
    nombre_formulario = "evidencia_form"
    mensaje_exito = "La fotografía fue agregada."

    def tiene_permiso(self, reporte, usuario):
        return reporte.puede_agregar_evidencia(usuario)

    def ejecutar(self, reporte, datos, usuario):
        reporte.agregar_evidencia(usuario, datos["imagen"], datos["descripcion"])


class CambiarEstadoView(AccionSobreReporteView):
    """RF09."""

    form_class = CambiarEstadoForm
    nombre_formulario = "estado_form"
    mensaje_exito = "El estado del reporte fue actualizado."

    def get_form_kwargs(self, reporte):
        return {"reporte": reporte}

    def tiene_permiso(self, reporte, usuario):
        return reporte.puede_gestionar(usuario)

    def ejecutar(self, reporte, datos, usuario):
        reporte.cambiar_estado(datos["estado"], usuario, datos["observacion"])


class RegistrarSeguimientoView(AccionSobreReporteView):
    """RF10."""

    form_class = SeguimientoForm
    nombre_formulario = "seguimiento_form"
    mensaje_exito = "El seguimiento fue registrado."

    def tiene_permiso(self, reporte, usuario):
        return reporte.puede_gestionar(usuario)

    def ejecutar(self, reporte, datos, usuario):
        reporte.registrar_seguimiento(usuario, datos["accion"], datos["descripcion"])


class AportarInformacionView(AccionSobreReporteView):
    """El ciudadano agrega información a su propio reporte mientras el caso está abierto."""

    form_class = AporteForm
    nombre_formulario = "aporte_form"
    mensaje_exito = "Tu información fue agregada al reporte."

    def tiene_permiso(self, reporte, usuario):
        return reporte.puede_aportar_informacion(usuario)

    def ejecutar(self, reporte, datos, usuario):
        reporte.aportar_informacion(usuario, datos["descripcion"])


class AsignarReporteView(AccionSobreReporteView):
    form_class = AsignarForm
    nombre_formulario = "asignar_form"
    mensaje_exito = "El reporte fue asignado a la institución."

    def tiene_permiso(self, reporte, usuario):
        return usuario.puede("asignar_reporte")

    def ejecutar(self, reporte, datos, usuario):
        reporte.asignar_a(datos["institucion"], usuario, datos["observacion"])
