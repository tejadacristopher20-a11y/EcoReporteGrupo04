"""Reglas adicionales de contraseña, además de las cuatro que trae Django.

Se registran en AUTH_PASSWORD_VALIDATORS (settings.py), por lo que se aplican al crear la cuenta,
al cambiar la contraseña y en createsuperuser. get_help_text() es lo que aparece en la lista de
requisitos debajo del campo de contraseña.
"""
from django.core.exceptions import ValidationError


class ContieneNumeroValidator:
    def validate(self, password, user=None):
        if not any(c.isdigit() for c in password):
            raise ValidationError(
                "La contraseña debe incluir al menos un número (0-9).", code="clave_sin_numero"
            )

    def get_help_text(self):
        return "Su contraseña debe incluir al menos un número (0-9)."


class ContieneSimboloValidator:
    def validate(self, password, user=None):
        if not any(not c.isalnum() and not c.isspace() for c in password):
            raise ValidationError(
                "La contraseña debe incluir al menos un símbolo, por ejemplo: - _ . @ # $ % & * !",
                code="clave_sin_simbolo",
            )

    def get_help_text(self):
        return "Su contraseña debe incluir al menos un símbolo, por ejemplo: - _ . @ # $ % & * !"
