import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def estatico(ruta):
    """Como {% static %}, pero agrega la fecha de modificación del archivo: estilos.css?v=1762620000.

    Cada vez que el archivo cambia, su dirección cambia, así el navegador descarga la versión nueva en lugar
    de seguir usando la copia vieja que tenía guardada (sin tener que recargar con Ctrl + F5).
    """
    url = static(ruta)
    archivo = finders.find(ruta)
    if archivo:
        url += ("&" if "?" in url else "?") + f"v={int(os.path.getmtime(archivo))}"
    return url
