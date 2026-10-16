from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from Eco_Reporte_Comunitario.formularios import EstiloBootstrapMixin

from .models import Ciudadano, Usuario


class RegistroForm(EstiloBootstrapMixin, UserCreationForm):
    """RF01: todo usuario que se registra desde la web es Ciudadano."""

    class Meta(UserCreationForm.Meta):
        model = Ciudadano
        fields = ("first_name", "last_name", "email", "telefono")
        labels = {"first_name": "Nombre", "last_name": "Apellido"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ("first_name", "last_name", "email"):
            self.fields[campo].required = True
        self.fields["first_name"].widget.attrs["autofocus"] = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo electrónico.")
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.username = usuario.email
        if commit:
            usuario.save()
        return usuario


class IngresoForm(EstiloBootstrapMixin, AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Correo o contraseña incorrectos.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Correo electrónico"


class PerfilForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ("first_name", "last_name", "telefono")
        labels = {"first_name": "Nombre", "last_name": "Apellido"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True


class CambiarClaveForm(EstiloBootstrapMixin, PasswordChangeForm):
    pass
