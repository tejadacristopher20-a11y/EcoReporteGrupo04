from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import CambiarClaveForm, IngresoForm, PerfilForm, RegistroForm


class RegistroView(CreateView):
    form_class = RegistroForm
    template_name = "appusuarios/registro.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("appreportes:panel")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        usuario = form.save()
        login(self.request, usuario, backend="appusuarios.backends.CorreoOUsuarioBackend")
        messages.success(self.request, f"¡Bienvenido, {usuario.first_name}! Tu cuenta fue creada.")
        return redirect("appreportes:panel")


class IngresoView(LoginView):
    form_class = IngresoForm
    template_name = "appusuarios/ingresar.html"
    redirect_authenticated_user = True


class SalidaView(LogoutView):
    pass


class PerfilView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = PerfilForm
    template_name = "appusuarios/perfil.html"
    success_url = reverse_lazy("appusuarios:perfil")
    success_message = "Tus datos fueron actualizados."

    def get_object(self, queryset=None):
        return self.request.user


class CambiarClaveView(SuccessMessageMixin, PasswordChangeView):
    form_class = CambiarClaveForm
    template_name = "appusuarios/cambiar_clave.html"
    success_url = reverse_lazy("appusuarios:perfil")
    success_message = "Tu contraseña fue cambiada."
