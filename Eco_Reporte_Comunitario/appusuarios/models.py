import copy

from django.apps import apps
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.functions import Now
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from Eco_Reporte_Comunitario.modelos_base import ModeloBase
from Eco_Reporte_Comunitario.restricciones import (
    q_correo,
    q_nombre_persona,
    q_telefono_opcional,
    q_valor_en,
    validar_nombre_persona,
    validar_telefono,
)


class Rol(models.TextChoices):
    CIUDADANO = "CIUDADANO", "Ciudadano"
    RESPONSABLE = "RESPONSABLE", "Responsable institucional"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"


class UsuarioManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # El superusuario es el administrador único del sistema.
        if Usuario.objects.filter(rol=Usuario.Rol.ADMINISTRADOR).exists():
            raise ValueError(Usuario.MENSAJE_ADMINISTRADOR_UNICO)
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

    Rol = Rol

    # Campos heredados de AbstractUser que se redefinen para agregar validación y DEFAULT en SQL Server.
    first_name = models.CharField(
        _("first name"), max_length=150, blank=True, db_default="", validators=[validar_nombre_persona]
    )
    last_name = models.CharField(
        _("last name"), max_length=150, blank=True, db_default="", validators=[validar_nombre_persona]
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        db_default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        db_default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_superuser = models.BooleanField(
        _("superuser status"),
        default=False,
        db_default=False,
        help_text=_(
            "Designates that this user has all permissions without "
            "explicitly assigning them."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now, db_default=Now())

    email = models.EmailField("correo electrónico", unique=True)
    rol = models.CharField(max_length=15, choices=Rol.choices, default=Rol.CIUDADANO, db_default=Rol.CIUDADANO)
    telefono = models.CharField(
        "teléfono", max_length=15, blank=True, db_default="", validators=[validar_telefono]
    )
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

    MENSAJE_ADMINISTRADOR_UNICO = "Ya existe un administrador. El sistema solo permite un administrador."

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        constraints = [
            models.CheckConstraint(
                condition=q_valor_en("rol", Rol.choices),
                name="ck_usuario_rol_valido",
                violation_error_message="El rol del usuario no es válido.",
            ),
            models.UniqueConstraint(
                fields=["rol"],
                condition=Q(rol=Rol.ADMINISTRADOR),
                name="uq_usuario_administrador_unico",
                violation_error_message="Ya existe un administrador. El sistema solo permite un administrador.",
            ),
            models.CheckConstraint(
                condition=Q(rol=Rol.ADMINISTRADOR) | Q(is_staff=False, is_superuser=False),
                name="ck_usuario_panel_solo_administrador",
                violation_error_message="Solo el administrador puede tener acceso al panel de administración.",
            ),
            models.CheckConstraint(
                condition=Q(rol=Rol.RESPONSABLE) | Q(institucion__isnull=True),
                name="ck_usuario_institucion_solo_responsable",
                violation_error_message="Solo los responsables pueden pertenecer a una institución.",
            ),
            models.CheckConstraint(
                condition=~Q(username=""),
                name="ck_usuario_username_requerido",
                violation_error_message="El nombre de usuario es obligatorio.",
            ),
            models.CheckConstraint(
                condition=q_correo("email"),
                name="ck_usuario_correo_valido",
                violation_error_message="El correo electrónico no es válido.",
            ),
            models.CheckConstraint(
                condition=Q(first_name="") | q_nombre_persona("first_name"),
                name="ck_usuario_nombre_valido",
                violation_error_message="El nombre solo admite letras y espacios.",
            ),
            models.CheckConstraint(
                condition=Q(last_name="") | q_nombre_persona("last_name"),
                name="ck_usuario_apellido_valido",
                violation_error_message="El apellido solo admite letras y espacios.",
            ),
            models.CheckConstraint(
                condition=q_telefono_opcional("telefono"),
                name="ck_usuario_telefono_valido",
                violation_error_message="El teléfono debe tener 8 números y, como máximo, un guion medio (ej. 7000-0000).",
            ),
        ]

    def __str__(self):
        return self.get_full_name() or self.username

    def existe_otro_administrador(self):
        return Usuario.objects.filter(rol=self.Rol.ADMINISTRADOR).exclude(pk=self.pk).exists()

    def validar_reglas_de_rol(self):
        """Reglas que se cumplen siempre, se guarde el usuario desde /admin/, la web o la terminal."""
        if self.rol == self.Rol.ADMINISTRADOR and self.existe_otro_administrador():
            raise ValidationError(self.MENSAJE_ADMINISTRADOR_UNICO)
        if (self.is_staff or self.is_superuser) and self.rol != self.Rol.ADMINISTRADOR:
            raise ValidationError("Solo el administrador puede tener acceso al panel de administración.")
        if self.rol != self.Rol.RESPONSABLE and self.institucion_id:
            raise ValidationError("Solo los responsables pueden pertenecer a una institución.")

    def clean(self):
        # Las reglas de rol se validan con las restricciones de Meta (validate_constraints).
        super().clean()
        if self.rol_fijo:
            self.rol = self.rol_fijo

    def save(self, *args, **kwargs):
        if self.rol_fijo:
            self.rol = self.rol_fijo
        self.validar_reglas_de_rol()
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
        # Sobre sus propios reportes; las condiciones de estado las aplica ReporteAmbiental.
        return frozenset({
            "crear_reporte",
            "consultar_reportes",
            "modificar_reporte_propio",
            "eliminar_reporte_propio",
            "agregar_evidencia",
            "aportar_informacion",
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
        # Coordinador: asigna los casos a las instituciones y les da seguimiento.
        return frozenset({
            "consultar_reportes",
            "asignar_reporte",
            "cambiar_estado",
            "registrar_seguimiento",
            "agregar_evidencia",
        })

    def reportes_de_panel(self):
        return _reportes().all()

    def titulo_panel(self):
        return "Casos de la comunidad"


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
            "gestionar_usuarios",
            "gestionar_catalogos",
        }

    def reportes_de_panel(self):
        return _reportes().all()

    def titulo_panel(self):
        return "Todos los reportes"
