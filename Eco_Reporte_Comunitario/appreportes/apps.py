from django.apps import AppConfig
from django.db.models import fields

# Django 6.1 aún no trae traducido al español el texto vacío de las listas de selección
# ("- Select an option -"); aquí se define para todo el proyecto.
# Va al cargar este archivo (y no en ready()) porque el panel de administración arranca primero y,
# al leer admin.py, ya arma los formularios: si el texto se cambiara después, quedaría en inglés.
fields.BLANK_CHOICE_LABEL = "- Seleccione una opción -"


class AppreportesConfig(AppConfig):
    name = 'appreportes'
    verbose_name = 'Reportes ambientales'
