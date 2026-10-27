from django.apps import AppConfig


class AppreportesConfig(AppConfig):
    name = 'appreportes'
    verbose_name = 'Reportes ambientales'

    def ready(self):
        # Django 6.1 aún no trae traducido al español el texto vacío de las listas
        # de selección ("- Select an option -"); aquí se define para todo el proyecto.
        from django.db.models import fields

        fields.BLANK_CHOICE_LABEL = "- Seleccione una opción -"
