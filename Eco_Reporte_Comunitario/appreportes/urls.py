from django.urls import path

from . import views

app_name = "appreportes"

urlpatterns = [
    path("", views.InicioView.as_view(), name="inicio"),
    path("reportes/", views.ReporteListView.as_view(), name="lista"),
    path("reportes/nuevo/", views.ReporteCreateView.as_view(), name="crear"),
    path("reportes/<int:pk>/", views.ReporteDetailView.as_view(), name="detalle"),
    path("reportes/<int:pk>/editar/", views.ReporteUpdateView.as_view(), name="editar"),
    path("reportes/<int:pk>/eliminar/", views.ReporteDeleteView.as_view(), name="eliminar"),
    path("reportes/<int:pk>/evidencia/", views.AgregarEvidenciaView.as_view(), name="agregar_evidencia"),
    path("reportes/<int:pk>/estado/", views.CambiarEstadoView.as_view(), name="cambiar_estado"),
    path("reportes/<int:pk>/seguimiento/", views.RegistrarSeguimientoView.as_view(), name="registrar_seguimiento"),
    path("reportes/<int:pk>/aporte/", views.AportarInformacionView.as_view(), name="aportar_informacion"),
    path("reportes/<int:pk>/asignar/", views.AsignarReporteView.as_view(), name="asignar"),
    path("mi-panel/", views.PanelView.as_view(), name="panel"),
]
