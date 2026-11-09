"""Reglas de formato de los datos, en un solo lugar.

Cada regla existe en dos niveles que comparten la misma definición:
- Validadores de Python: los formularios muestran un mensaje claro al usuario.
- Condiciones para CheckConstraint: SQL Server rechaza el dato aunque se inserte
  directamente con SQL, sin pasar por la aplicación.
"""
import re
from decimal import Decimal

from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models import CharField, DateField, F, Func, Lookup, Q, Value
from django.db.models.functions import Length, Replace
from django.db.models.lookups import GreaterThanOrEqual, LessThanOrEqual
from django.utils.deconstruct import deconstructible


def patron_like_a_regex(patron):
    """Traduce un patrón LIKE de SQL Server (con %, _ y clases [...]) a una expresión regular equivalente.

    «%[A-Z]%» → «^.*[A-Z].*$». Las clases [...] y [^...] se escriben igual en las dos sintaxis; el resto de
    los caracteres se toman literalmente. Así la misma restricción funciona en SQL Server y en PostgreSQL.
    """
    partes, i = [], 0
    while i < len(patron):
        caracter = patron[i]
        if caracter == "[":
            fin = patron.index("]", i + 1)
            partes.append(patron[i:fin + 1])
            i = fin + 1
            continue
        partes.append(".*" if caracter == "%" else "." if caracter == "_" else re.escape(caracter))
        i += 1
    return "^" + "".join(partes) + "$"


@CharField.register_lookup
class Like(Lookup):
    """campo__like='patrón' genera «campo LIKE 'patrón'» (comodines y clases [...] de SQL Server).

    En PostgreSQL, LIKE no entiende las clases [...]: ahí se traduce a una expresión regular (operador ~)
    que acepta y rechaza exactamente los mismos textos.
    """

    lookup_name = "like"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        return f"{lhs} LIKE {rhs}", (*lhs_params, *rhs_params)

    def as_postgresql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        rhs_params = [patron_like_a_regex(p) if isinstance(p, str) else p for p in rhs_params]
        return f"{lhs}::text ~ {rhs}", (*lhs_params, *rhs_params)


class RestarAnios(Func):
    """RestarAnios(fecha, 1) genera «DATEADD(year, -1, fecha)» de SQL Server.

    En PostgreSQL se escribe «fecha - INTERVAL '1 years'». En los dos, el 29 de febrero pasa al 28.
    """

    function = "DATEADD"
    template = "%(function)s(year, -%(anios)d, %(expressions)s)"
    output_field = DateField()

    def __init__(self, expresion, anios=1, **extra):
        super().__init__(expresion, anios=anios, **extra)

    def as_postgresql(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler, connection, template="CAST((%(expressions)s - INTERVAL '%(anios)d years') AS date)",
            **extra_context,
        )


def restar_anios(fecha, anios=1):
    """Lo mismo que RestarAnios, en Python. El 29 de febrero pasa al 28, igual que DATEADD."""
    try:
        return fecha.replace(year=fecha.year - anios)
    except ValueError:
        return fecha.replace(year=fecha.year - anios, day=28)


LETRAS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"

# Nombres de personas: letras, espacios, punto, apóstrofo y guion.
SIMBOLOS_NOMBRE_PERSONA = " .'-"
# Nombres de lugares, catálogos e instituciones: además números, coma y paréntesis.
SIMBOLOS_NOMBRE_GENERAL = "0-9 .,'()-"

MINIMO_DIGITOS_TELEFONO = 8
MAXIMO_DIGITOS_TELEFONO = 8  # Los teléfonos de El Salvador tienen 8 dígitos.

# --- Textos libres (título, descripción, referencia, seguimiento, observaciones) ---
# Signos permitidos además de letras y números. El guion va al final para que,
# dentro de una clase [...] de LIKE o de una expresión regular, sea un carácter literal.
SIGNOS_TEXTO_LIBRE = " .,;:¿?¡!()\"'/#-"
SIGNOS_TEXTO_LIBRE_VISIBLES = ". , ; : ¿ ? ¡ ! ( ) - \" ' / #"
VOCALES = "aeiouáéíóúüAEIOUÁÉÍÓÚÜ"
PORCENTAJE_MINIMO_LETRAS = 60
MAXIMO_REPETICIONES_SEGUIDAS = 3
MAXIMO_DIGITOS_REPETIDOS = 4  # Permite teléfonos y cantidades como 7000-0000 o 10000.
MAXIMO_LARGO_PALABRA = 25
LARGO_PALABRA_QUE_EXIGE_VOCAL = 4
MAXIMO_DIGITOS_SEGUIDOS = 8

# Mínimos de cada campo: (caracteres, palabras).
MINIMO_TITULO_REPORTE = (8, 2)
MINIMO_DESCRIPCION_REPORTE = (15, 3)
MINIMO_REFERENCIA = (5, 2)
MINIMO_ACCION_SEGUIMIENTO = (3, 1)
MINIMO_DESCRIPCION_SEGUIMIENTO = (10, 2)
MINIMO_OBSERVACION = (5, 1)
MINIMO_DESCRIPCION_FOTO = (3, 1)
MINIMO_DESCRIPCION_CATEGORIA = (10, 2)

# --- Coordenadas: el territorio de El Salvador (aproximado, incluye las islas del golfo de Fonseca) ---
LATITUD_MINIMA = Decimal("13.1")
LATITUD_MAXIMA = Decimal("14.5")
LONGITUD_MINIMA = Decimal("-90.2")
LONGITUD_MAXIMA = Decimal("-87.6")

# --- Reportes ---
ANIOS_MAXIMOS_INCIDENTE = 5  # La fecha del incidente puede ser de hasta 5 años antes del reporte.
MAXIMO_EVIDENCIAS_POR_REPORTE = 5  # Ciudadano y administrador.
MAXIMO_EVIDENCIAS_RESPONSABLE = 10  # El responsable documenta el avance del caso con más fotos.
# Un reporte con los mismos datos, del mismo usuario y dentro de estos minutos se toma como el mismo
# reporte enviado otra vez (por ejemplo, al volver «Atrás» y guardar de nuevo).
MINUTOS_REPORTE_DUPLICADO = 10


# --- Validadores para los formularios ---

validar_contiene_letras = RegexValidator(
    rf"[{LETRAS}]",
    "Escriba un texto que incluya letras; no se aceptan solo números o símbolos.",
)

validar_nombre_persona = RegexValidator(
    rf"^[{LETRAS}][{LETRAS}{re.escape(SIMBOLOS_NOMBRE_PERSONA)}]*$",
    "Use solo letras y espacios.",
)

validar_nombre_general = RegexValidator(
    rf"^(?=.*[{LETRAS}])[{LETRAS}0-9 .,'()\-]+$",
    "Use letras, números, espacios y los signos . , ' ( ) -",
)


_RE_CARACTER_PERMITIDO = re.compile(rf"[{LETRAS}0-9\r\n{re.escape(SIGNOS_TEXTO_LIBRE)}]")
_RE_LETRA = re.compile(rf"[{LETRAS}]")
_RE_PALABRA_DE_LETRAS = re.compile(rf"[{LETRAS}]+")
_RE_VOCAL = re.compile(rf"[{VOCALES}]")
_RE_REPETICION = re.compile(
    rf"([^\s0-9])\1{{{MAXIMO_REPETICIONES_SEGUIDAS},}}|([0-9])\2{{{MAXIMO_DIGITOS_REPETIDOS},}}"
)
_RE_DIGITOS_SEGUIDOS = re.compile(rf"[0-9]{{{MAXIMO_DIGITOS_SEGUIDOS + 1},}}")
# La misma sílaba de 2 o 3 letras, 3 veces o más seguidas: «erererer», «tatata», «asdasdasd».
_RE_SILABA_REPETIDA = re.compile(rf"([{LETRAS}]{{2,3}})\1{{2,}}", re.IGNORECASE)
_RE_LETRA_Y_DIGITO = re.compile(rf"[{LETRAS}][0-9]|[0-9][{LETRAS}]")
# Ordinales permitidos aunque mezclan números y letras: 1ro, 2da, 3er, 10mo…
_RE_ORDINAL = re.compile(r"[0-9]+(ro|ra|do|da|er|to|ta|vo|va|no|na|mo|ma)", re.IGNORECASE)
_RE_SIGNOS_EXTREMOS = re.compile(r"^[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+|[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+$")


@deconstructible
class ValidadorTextoLibre:
    """Detecta texto sin sentido: símbolos raros, cadenas de números, teclazos y letras repetidas.

    Reúne todas las reglas que no se cumplen para que el usuario vea, debajo del campo,
    exactamente qué debe corregir.
    """

    def __init__(self, minimo_caracteres=1, minimo_palabras=1):
        self.minimo_caracteres = minimo_caracteres
        self.minimo_palabras = minimo_palabras

    def __call__(self, valor):
        texto = valor.strip()
        errores = []

        prohibidos = sorted({c for c in texto if not _RE_CARACTER_PERMITIDO.fullmatch(c)})
        if prohibidos:
            errores.append(
                f"No se permiten estos caracteres: {' '.join(prohibidos)}. "
                f"Use solo letras, números y los signos {SIGNOS_TEXTO_LIBRE_VISIBLES}"
            )

        if len(texto) < self.minimo_caracteres:
            errores.append(f"Escriba al menos {self.minimo_caracteres} caracteres (lleva {len(texto)}).")

        palabras = [p for p in texto.split() if re.search(rf"[{LETRAS}0-9]", p)]
        if len(palabras) < self.minimo_palabras:
            plural = "palabra" if self.minimo_palabras == 1 else "palabras"
            errores.append(f"Escriba al menos {self.minimo_palabras} {plural} (lleva {len(palabras)}).")

        sin_espacios = [c for c in texto if not c.isspace()]
        letras = sum(1 for c in sin_espacios if _RE_LETRA.fullmatch(c))
        if not letras:
            errores.append("El texto debe incluir letras; no se aceptan solo números o símbolos.")
        elif letras * 100 < PORCENTAJE_MINIMO_LETRAS * len(sin_espacios):
            porcentaje = letras * 100 // len(sin_espacios)
            errores.append(
                f"El texto debe estar formado principalmente por letras: al menos el "
                f"{PORCENTAJE_MINIMO_LETRAS} % de los caracteres (ahora es el {porcentaje} %)."
            )

        repeticion = _RE_REPETICION.search(texto)
        if repeticion:
            errores.append(
                f"No repita el mismo carácter tantas veces seguidas (máximo {MAXIMO_REPETICIONES_SEGUIDAS} "
                f"letras o signos, o {MAXIMO_DIGITOS_REPETIDOS} números iguales): «{repeticion.group(0)[:8]}»."
            )

        larga = next((p for p in texto.split() if len(p) > MAXIMO_LARGO_PALABRA), None)
        if larga:
            errores.append(
                f"La palabra «{larga[:20]}…» es demasiado larga: máximo {MAXIMO_LARGO_PALABRA} caracteres por palabra."
            )

        if _RE_DIGITOS_SEGUIDOS.search(texto):
            errores.append(f"No escriba más de {MAXIMO_DIGITOS_SEGUIDOS} números seguidos.")

        silaba = _RE_SILABA_REPETIDA.search(texto)
        if silaba:
            errores.append(
                f"«{silaba.group(0)[:12]}» repite la misma sílaba muchas veces seguidas; escriba palabras reales."
            )

        mezcladas = [
            limpia for limpia in (_RE_SIGNOS_EXTREMOS.sub("", p) for p in texto.split())
            if _RE_LETRA_Y_DIGITO.search(limpia) and not _RE_ORDINAL.fullmatch(limpia)
        ]
        if mezcladas:
            errores.append(
                f"«{mezcladas[0][:20]}» mezcla letras y números en la misma palabra; "
                "sepárelos con un espacio (ejemplo: «Casa 12»)."
            )

        sin_vocal = [
            p for p in _RE_PALABRA_DE_LETRAS.findall(texto)
            if len(p) >= LARGO_PALABRA_QUE_EXIGE_VOCAL and not p.isupper() and not _RE_VOCAL.search(p)
        ]
        if sin_vocal:
            errores.append(
                f"«{sin_vocal[0]}» no parece una palabra: las palabras de "
                f"{LARGO_PALABRA_QUE_EXIGE_VOCAL} letras o más deben llevar al menos una vocal."
            )

        if errores:
            raise ValidationError(errores, code="texto_invalido")

    def __eq__(self, otro):
        return (
            isinstance(otro, ValidadorTextoLibre)
            and self.minimo_caracteres == otro.minimo_caracteres
            and self.minimo_palabras == otro.minimo_palabras
        )


def validador_texto(minimos):
    """validador_texto(MINIMO_TITULO_REPORTE) → ValidadorTextoLibre(8, 2)."""
    return ValidadorTextoLibre(*minimos)


def validar_telefono(valor):
    """Solo números, con un único guion medio opcional entre ellos, y exactamente 8 dígitos (ej. 7000-0000)."""
    errores = []
    if re.search(r"[^0-9-]", valor):
        errores.append("Escriba solo números y, si desea, un único guion medio (-). Ej.: 7000-0000.")
    if valor.count("-") > 1:
        errores.append("Use un único guion medio (-); no se permiten varios guiones.")
    elif valor.startswith("-") or valor.endswith("-"):
        errores.append("El guion medio debe ir entre los números (ej. 7000-0000), no al inicio ni al final.")
    digitos = len(re.sub(r"[^0-9]", "", valor))
    if digitos < MINIMO_DIGITOS_TELEFONO:
        errores.append(f"El teléfono debe tener {MINIMO_DIGITOS_TELEFONO} números (lleva {digitos}).")
    elif digitos > MAXIMO_DIGITOS_TELEFONO:
        errores.append(f"El teléfono admite como máximo {MAXIMO_DIGITOS_TELEFONO} números (lleva {digitos}).")
    if errores:
        raise ValidationError(errores, code="telefono_invalido")


# --- Condiciones para las restricciones CHECK ---

def q_contiene_letras(campo):
    """Al menos una letra: evita textos vacíos, solo espacios, solo números o solo símbolos."""
    return Q(**{f"{campo}__like": f"%[{LETRAS}]%"})


def q_texto_opcional(campo):
    """Campo opcional: vacío, o con letras si se escribe algo."""
    return Q(**{campo: ""}) | q_contiene_letras(campo)


def q_nombre_persona(campo):
    return Q(**{f"{campo}__like": f"[{LETRAS}]%"}) & ~Q(
        **{f"{campo}__like": f"%[^{LETRAS}{SIMBOLOS_NOMBRE_PERSONA}]%"}
    )


def q_nombre_general(campo):
    return q_contiene_letras(campo) & ~Q(**{f"{campo}__like": f"%[^{LETRAS}{SIMBOLOS_NOMBRE_GENERAL}]%"})


def q_telefono_opcional(campo):
    """Vacío, o solo dígitos con un único guion opcional en medio y exactamente 8 dígitos."""
    digitos = Length(Replace(F(campo), Value("-"), Value("")))
    return Q(**{campo: ""}) | (
        ~Q(**{f"{campo}__like": "%[^0-9-]%"})
        & ~Q(**{f"{campo}__like": "%-%-%"})
        & ~Q(**{f"{campo}__like": "-%"})
        & ~Q(**{f"{campo}__like": "%-"})
        & Q(GreaterThanOrEqual(digitos, MINIMO_DIGITOS_TELEFONO))
        & Q(LessThanOrEqual(digitos, MAXIMO_DIGITOS_TELEFONO))
    )


def q_correo(campo):
    """Forma básica de un correo: algo@dominio.ext, sin espacios."""
    return Q(**{f"{campo}__like": "%_@_%._%"}) & ~Q(**{f"{campo}__like": "% %"})


def q_valor_en(campo, opciones):
    return Q(**{f"{campo}__in": [valor for valor, _ in opciones]})


def q_longitud_minima(campo, minimo):
    """Cada «_» de LIKE equivale a un carácter: «__________%» exige al menos 10."""
    return Q(**{f"{campo}__like": "_" * minimo + "%"})


def q_texto_libre(campo, minimos):
    """Las reglas del ValidadorTextoLibre que SQL Server puede comprobar con LIKE.

    El porcentaje de letras, las repeticiones, las vocales y el número de palabras
    solo se validan en Python (formularios), porque LIKE no puede contarlos.
    """
    minimo_caracteres, _ = minimos
    return (
        q_contiene_letras(campo)
        & q_longitud_minima(campo, minimo_caracteres)
        & ~Q(**{f"{campo}__like": f"%[^{LETRAS}0-9\r\n{SIGNOS_TEXTO_LIBRE}]%"})
        & ~Q(**{f"{campo}__like": "%" + "[0-9]" * (MAXIMO_DIGITOS_SEGUIDOS + 1) + "%"})
        & ~Q(**{f"{campo}__like": "%" + "[^ \r\n]" * (MAXIMO_LARGO_PALABRA + 1) + "%"})
    )


def q_texto_libre_opcional(campo, minimos):
    """Campo opcional: vacío, o un texto libre válido."""
    return Q(**{campo: ""}) | q_texto_libre(campo, minimos)


def mensaje_restriccion_violada(error):
    """Traduce un IntegrityError de SQL Server al mensaje de la restricción que se violó.

    Es la red de seguridad: si un dato inválido llega hasta la base de datos, el usuario
    ve el mensaje claro de la restricción y no la página de error.
    """
    texto = str(error)
    for modelo in apps.get_models():
        for restriccion in modelo._meta.constraints:
            if restriccion.name in texto:
                return restriccion.violation_error_message or "Los datos no cumplen las reglas del sistema."
    return "No se pudo guardar la información porque no cumple las reglas del sistema. Revise los datos."
