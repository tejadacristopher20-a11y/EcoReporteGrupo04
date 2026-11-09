"""Fotografías guardadas dentro de la base de datos (se usa en Render).

En Render, el disco del servidor se borra en cada despliegue o reinicio, así que las fotos subidas se perderían.
Este almacenamiento las guarda en la tabla ArchivoGuardado (PostgreSQL) y las muestra en /media/<nombre>,
la misma dirección que se usa en la computadora local. Se activa en settings.py (STORAGES) solo en Render.
"""
import mimetypes
from urllib.parse import quote

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.http import Http404, HttpResponse
from django.utils.deconstruct import deconstructible


def _modelo():
    return apps.get_model("appreportes", "ArchivoGuardado")


def _normalizar(nombre):
    # Siempre con «/» (en Windows, Django arma las rutas con «\»).
    return str(nombre).replace("\\", "/")


@deconstructible
class AlmacenamientoEnBaseDeDatos(Storage):
    def _open(self, name, mode="rb"):
        archivo = _modelo().objects.filter(nombre=_normalizar(name)).first()
        if archivo is None:
            raise FileNotFoundError(name)
        return ContentFile(bytes(archivo.contenido), name=name)

    def _save(self, name, content):
        name = _normalizar(name)
        if hasattr(content, "seek"):
            content.seek(0)
        datos = content.read()
        _modelo().objects.create(
            nombre=name, contenido=datos, tipo=mimetypes.guess_type(name)[0] or "", tamano=len(datos)
        )
        return name

    def exists(self, name):
        return _modelo().objects.filter(nombre=_normalizar(name)).exists()

    def delete(self, name):
        if name:
            _modelo().objects.filter(nombre=_normalizar(name)).delete()

    def size(self, name):
        tamano = _modelo().objects.filter(nombre=_normalizar(name)).values_list("tamano", flat=True).first()
        if tamano is None:
            raise FileNotFoundError(name)
        return tamano

    def url(self, name):
        return "/" + settings.MEDIA_URL.strip("/") + "/" + quote(_normalizar(name))


def servir_archivo(request, nombre):
    """Muestra una fotografía guardada en la base de datos (/media/<nombre>)."""
    archivo = _modelo().objects.filter(nombre=_normalizar(nombre)).first()
    if archivo is None:
        raise Http404("La fotografía no existe.")
    respuesta = HttpResponse(bytes(archivo.contenido), content_type=archivo.tipo or "application/octet-stream")
    # Cada foto tiene un nombre único y no cambia: el navegador la puede guardar mucho tiempo.
    respuesta["Cache-Control"] = "public, max-age=31536000, immutable"
    return respuesta
