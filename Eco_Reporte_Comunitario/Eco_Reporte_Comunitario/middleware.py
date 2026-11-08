from django.utils.cache import add_never_cache_headers


class SinCopiaDePaginasPrivadasMiddleware:
    """Pide al navegador que no guarde copia de las páginas que ve un usuario con sesión iniciada.

    Así, al cerrar sesión y presionar «Atrás», el navegador vuelve a pedir la página al servidor (que lleva a
    «Iniciar sesión») en lugar de mostrar la copia con los datos personales. Importante en computadoras
    compartidas. Las páginas de los visitantes y los archivos estáticos (CSS, JS, íconos) no cambian.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        usuario = getattr(request, "user", None)
        # Si la página ya trae su propia instrucción de caché (por ejemplo, las del panel de administración), se respeta.
        if usuario is not None and usuario.is_authenticated and not response.has_header("Cache-Control"):
            add_never_cache_headers(response)
        return response
