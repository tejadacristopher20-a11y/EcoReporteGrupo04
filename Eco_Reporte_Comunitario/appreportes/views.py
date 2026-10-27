from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

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


class ReporteDetailView(DetailView):
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


class ReporteCreateView(PermisoRequeridoMixin, CreateView):
    """RF02."""

    permiso_requerido = "crear_reporte"
    form_class = ReporteForm
    template_name = "appreportes/reporte_form.html"
    extra_context = {"titulo_pagina": "Nuevo reporte"}

    def form_valid(self, form):
        self.object = form.guardar(self.request.user)
        messages.success(self.request, "Tu reporte fue registrado. ¡Gracias por cuidar tu comunidad!")
        return redirect(self.object)


class ReporteUpdateView(LoginRequiredMixin, UpdateView):
    """RF07."""

    model = ReporteAmbiental
    form_class = ReporteForm
    template_name = "appreportes/reporte_form.html"
    extra_context = {"titulo_pagina": "Editar reporte"}

    def get_object(self, queryset=None):
        reporte = super().get_object(queryset)
        if not reporte.puede_modificar(self.request.user):
            raise PermissionDenied
        return reporte

    def form_valid(self, form):
        self.object = form.guardar(self.request.user)
        messages.success(self.request, "El reporte fue actualizado.")
        return redirect(self.object)


class ReporteDeleteView(LoginRequiredMixin, DeleteView):
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


class AccionSobreReporteView(LoginRequiredMixin, View):
    """Clase base (patrón plantilla) para las acciones que se envían desde el detalle del reporte."""

    http_method_names = ["post"]
    form_class = None
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
                self.ejecutar(reporte, form.cleaned_data, request.user)
                messages.success(request, self.mensaje_exito)
            except ValidationError as error:
                messages.error(request, " ".join(error.messages))
        else:
            for errores in form.errors.values():
                messages.error(request, " ".join(errores))
        return redirect(reporte)


class AgregarEvidenciaView(AccionSobreReporteView):
    """RF05."""

    form_class = EvidenciaForm
    mensaje_exito = "La fotografía fue agregada."

    def tiene_permiso(self, reporte, usuario):
        return reporte.puede_agregar_evidencia(usuario)

    def ejecutar(self, reporte, datos, usuario):
        reporte.agregar_evidencia(usuario, datos["imagen"], datos["descripcion"])


class CambiarEstadoView(AccionSobreReporteView):
    """RF09."""

    form_class = CambiarEstadoForm
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
    mensaje_exito = "El seguimiento fue registrado."

    def tiene_permiso(self, reporte, usuario):
        return reporte.puede_gestionar(usuario)

    def ejecutar(self, reporte, datos, usuario):
        reporte.registrar_seguimiento(usuario, datos["accion"], datos["descripcion"])


class AportarInformacionView(AccionSobreReporteView):
    """El ciudadano agrega información a su propio reporte mientras el caso está abierto."""

    form_class = AporteForm
    mensaje_exito = "Tu información fue agregada al reporte."

    def tiene_permiso(self, reporte, usuario):
        return reporte.puede_aportar_informacion(usuario)

    def ejecutar(self, reporte, datos, usuario):
        reporte.aportar_informacion(usuario, datos["descripcion"])


class AsignarReporteView(AccionSobreReporteView):
    form_class = AsignarForm
    mensaje_exito = "El reporte fue asignado a la institución."

    def tiene_permiso(self, reporte, usuario):
        return usuario.puede("asignar_reporte")

    def ejecutar(self, reporte, datos, usuario):
        reporte.asignar_a(datos["institucion"], usuario, datos["observacion"])
