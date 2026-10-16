from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class CorreoOUsuarioBackend(ModelBackend):
    """Permite iniciar sesión con el correo electrónico o con el nombre de usuario."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        Usuario = get_user_model()
        if username is None:
            username = kwargs.get(Usuario.USERNAME_FIELD)
        if not username or not password:
            return None

        usuario = (
            Usuario._default_manager.filter(Q(email__iexact=username) | Q(username__iexact=username))
            .order_by("pk")
            .first()
        )
        if usuario is None:
            # Igual que ModelBackend: gasta el mismo tiempo para no revelar si el usuario existe.
            Usuario().set_password(password)
            return None
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
