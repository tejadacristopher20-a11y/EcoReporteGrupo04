import copy

from django.apps import apps
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models

from Eco_Reporte_Comunitario.modelos_base import ModeloBase


class UsuarioManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("rol", Usuario.Rol.ADMINISTRADOR)
        return super().create_superuser(username, email, password, **extra_fields)


class RolManager(UsuarioManager):
    """Manager de los proxies: cada uno solo ve a los usuarios de su rol."""

    use_in_migrations = False

    def __init__(self, rol):
        super().__init__()
        self.rol = rol

    def get_queryset(self):
        return super().get_queryset().filter(rol=self.rol)


class Usuario(AbstractUser, ModeloBase):
    """Entidad 1. Hereda de AbstractUser el login y el cifrado de contraseñas."""

    class Rol(models.TextChoices):
        CIUDADANO = "CIUDADANO", "Ciudadano"
        RESPONSABLE = "RESPONSABLE", "Responsable institucional"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    email = models.EmailField("correo electrónico", unique=True)
    rol = models.CharField(max_length=15, choices=Rol.choices, default=Rol.CIUDADANO)
    telefono = models.CharField("teléfono", max_length=15, blank=True)
    institucion = models.ForeignKey(
        "appinstituciones.Institucion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responsables",
        verbose_name="institución",
    )

    objects = UsuarioManager()

    # Los proxies fijan aquí su rol para que se guarde automáticamente.
    rol_fijo = None

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.get_full_name() or self.username

    def clean(self):
        super().clean()
        if self.rol == self.Rol.RESPONSABLE and not self.institucion_id:
            raise ValidationError({"institucion": "Un responsable debe pertenecer a una institución."})
        if self.rol != self.Rol.RESPONSABLE and self.institucion_id:
            raise ValidationError({"institucion": "Solo los responsables pertenecen a una institución."})

    def save(self, *args, **kwargs):
        if self.rol_fijo:
            self.rol = self.rol_fijo
        super().save(*args, **kwargs)

    def como_rol(self):
        """Devuelve este mismo usuario como instancia de la clase de su rol."""
        clase = {
            self.Rol.CIUDADANO: Ciudadano,
            self.Rol.RESPONSABLE: Responsable,
            self.Rol.ADMINISTRADOR: Administrador,
        }[self.rol]
        if isinstance(self, clase):
            return self
        instancia = copy.copy(self)
        instancia.__class__ = clase
        return instancia

    def obtener_permisos(self):
        """Método polimórfico: cada rol lo sobrescribe."""
        return self.como_rol().obtener_permisos()

    def puede(self, permiso):
        return permiso in self.obtener_permisos()

    def reportes_de_panel(self):
        """Método polimórfico: qué reportes ve cada rol en "Mi panel"."""
        return self.como_rol().reportes_de_panel()

    def titulo_panel(self):
        return self.como_rol().titulo_panel()


def _reportes():
    # Import diferido para evitar la importación circular entre apps.
    return apps.get_model("appreportes", "ReporteAmbiental").objects


class Ciudadano(Usuario):
    rol_fijo = Usuario.Rol.CIUDADANO
    objects = RolManager(Usuario.Rol.CIUDADANO)

    class Meta:
        proxy = True
        verbose_name = "ciudadano"
        verbose_name_plural = "ciudadanos"

    def obtener_permisos(self):
        return frozenset({
            "crear_reporte",
            "consultar_reportes",
            "modificar_reporte_propio",
            "eliminar_reporte_propio",
            "agregar_evidencia",
        })

    def reportes_de_panel(self):
        return _reportes().filter(usuario=self)

    def titulo_panel(self):
        return "Mis reportes"


class Responsable(Usuario):
    rol_fijo = Usuario.Rol.RESPONSABLE
    objects = RolManager(Usuario.Rol.RESPONSABLE)

    class Meta:
        proxy = True
        verbose_name = "responsable institucional"
        verbose_name_plural = "responsables institucionales"

    def obtener_permisos(self):
        return frozenset({
            "consultar_reportes",
            "registrar_seguimiento",
            "cambiar_estado",
            "agregar_evidencia",
        })

    def reportes_de_panel(self):
        if not self.institucion_id:
            return _reportes().none()
        return _reportes().filter(asignaciones__institucion=self.institucion_id, asignaciones__activa=True)

    def titulo_panel(self):
        return f"Casos asignados a {self.institucion}" if self.institucion_id else "Casos asignados"


class Administrador(Usuario):
    rol_fijo = Usuario.Rol.ADMINISTRADOR
    objects = RolManager(Usuario.Rol.ADMINISTRADOR)

    class Meta:
        proxy = True
        verbose_name = "administrador"
        verbose_name_plural = "administradores"

    def obtener_permisos(self):
        return Ciudadano.obtener_permisos(self) | Responsable.obtener_permisos(self) | {
            "modificar_cualquier_reporte",
            "eliminar_cualquier_reporte",
            "asignar_reporte",
            "gestionar_usuarios",
            "gestionar_catalogos",
        }

    def reportes_de_panel(self):
        return _reportes().all()

    def titulo_panel(self):
        return "Todos los reportes"
