from django.contrib import messages
from django.shortcuts import redirect


def csrf_fallido(request, reason=""):
    """Formulario con el código de seguridad vencido (por ejemplo, se volvió «Atrás» después de
    iniciar o cerrar sesión y se envió la copia vieja de la página).

    En lugar de la página técnica «Prohibido (403)», vuelve a abrir la misma dirección con un aviso.
    Esa recarga solo muestra la página (no repite el envío) y trae el código de seguridad nuevo.
    """
    messages.warning(
        request,
        "La página había expirado (por ejemplo, porque iniciaste o cerraste sesión) y no se envió nada. "
        "Te mostramos la página actualizada; vuelve a intentarlo si hace falta.",
    )
    return redirect(request.get_full_path())
