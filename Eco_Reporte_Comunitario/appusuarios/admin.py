from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from Eco_Reporte_Comunitario.admin_base import AvisoEliminadoAdminMixin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(AvisoEliminadoAdminMixin, UserAdmin):
    list_display = ("username", "first_name", "last_name", "email", "rol", "institucion", "is_active")
    list_filter = ("rol", "is_active", "institucion")
    fieldsets = UserAdmin.fieldsets + (
        ("EcoReporte", {"fields": ("rol", "telefono", "institucion")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("EcoReporte", {"fields": ("email", "first_name", "last_name", "rol", "telefono", "institucion")}),
    )
