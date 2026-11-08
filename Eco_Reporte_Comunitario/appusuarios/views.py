from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.db import IntegrityError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, UpdateView

from .forms import CambiarClaveForm, IngresoForm, PerfilForm, RegistroForm
from .models import Usuario

BACKEND_INGRESO = "appusuarios.backends.CorreoOUsuarioBackend"


class RegistroView(CreateView):
    form_class = RegistroForm
    template_name = "appusuarios/registro.html"

    # Tiempo en el que un segundo envío del mismo formulario se considera un doble clic.
    VENTANA_DOBLE_CLIC = timedelta(minutes=2)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("appreportes:panel")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            usuario = form.save()
        except IntegrityError:
            # Dos clics al mismo tiempo: SQL Server rechazó el segundo por el correo repetido.
            return self.form_invalid(form)
        login(self.request, usuario, backend=BACKEND_INGRESO)
        messages.success(self.request, f"¡Bienvenido, {usuario.first_name}! Tu cuenta fue creada.")
        return redirect("appreportes:panel")

    def form_invalid(self, form):
        usuario = self.cuenta_recien_creada(form)
        if usuario:
            login(self.request, usuario, backend=BACKEND_INGRESO)
            messages.info(self.request, "Tu cuenta ya se había creado; iniciaste sesión.")
            return redirect("appreportes:panel")
        return super().form_invalid(form)

    def cuenta_recien_creada(self, form):
        """La cuenta que se acaba de crear con este mismo formulario (doble clic), si existe.

        Exige la misma contraseña, así que nadie puede entrar a una cuenta ajena con este formulario.
        """
        correo = (form.data.get("email") or "").strip().lower()
        clave = form.data.get("password1") or ""
        if not correo or not clave:
            return None
        usuario = Usuario.objects.filter(email__iexact=correo).first()
        if (
            usuario
            and usuario.is_active
            and timezone.now() - usuario.date_joined < self.VENTANA_DOBLE_CLIC
            and usuario.check_password(clave)
        ):
            return usuario
        return None


class IngresoView(LoginView):
    form_class = IngresoForm
    template_name = "appusuarios/ingresar.html"
    redirect_authenticated_user = True


class SalidaView(LogoutView):
    """Cerrar sesión solo con el botón (POST). Si la dirección se abre como página, lleva al inicio
    sin cerrar la sesión, en lugar de mostrar el error 405."""

    http_method_names = ["get", "post", "options"]

    def get(self, request, *args, **kwargs):
        return redirect("appreportes:inicio")


class SalidaAdminView(View):
    """/admin/logout/: el botón «Cerrar sesión» del panel sigue funcionando igual (POST);
    si la dirección se abre como página, vuelve al panel en lugar de mostrar el error 405."""

    def get(self, request):
        return redirect("admin:index")

    def post(self, request):
        return admin.site.logout(request)


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
