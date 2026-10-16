from django.urls import path

from . import views

app_name = "appusuarios"

urlpatterns = [
    path("registro/", views.RegistroView.as_view(), name="registro"),
    path("ingresar/", views.IngresoView.as_view(), name="ingresar"),
    path("salir/", views.SalidaView.as_view(), name="salir"),
    path("perfil/", views.PerfilView.as_view(), name="perfil"),
    path("perfil/clave/", views.CambiarClaveView.as_view(), name="cambiar_clave"),
]
