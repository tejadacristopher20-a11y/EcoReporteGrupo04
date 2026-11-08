import io
import os
import uuid

from django import forms
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageOps

from Eco_Reporte_Comunitario.formularios import EstiloBootstrapMixin
from Eco_Reporte_Comunitario.restricciones import (
    ANIOS_MAXIMOS_INCIDENTE,
    LATITUD_MAXIMA,
    LATITUD_MINIMA,
    LONGITUD_MAXIMA,
    LONGITUD_MINIMA,
    MAXIMO_EVIDENCIAS_POR_REPORTE,
    MINIMO_DESCRIPCION_REPORTE,
    MINIMO_REFERENCIA,
    MINIMO_TITULO_REPORTE,
)

from appinstituciones.models import AsignacionReporte, Institucion
from appterritorio.models import Comunidad, Ubicacion

from .models import CategoriaProblema, Evidencia, HistorialEstado, ReporteAmbiental, Seguimiento


def campo_del_modelo(modelo, nombre, **kwargs):
    """Campo de formulario con las mismas validaciones que el campo del modelo.

    formfield() no copia los validadores propios del modelo (por ejemplo, el de texto libre),
    así que se agregan aquí; sin ellos, el dato inválido llegaría hasta SQL Server.
    """
    campo_modelo = modelo._meta.get_field(nombre)
    campo = campo_modelo.formfield(**kwargs)
    tipos_existentes = {type(v) for v in campo.validators}
    campo.validators += [v for v in campo_modelo.validators if type(v) not in tipos_existentes]
    return campo


TAMANO_MAXIMO_FOTO = 5 * 1024 * 1024  # 5 MB


def validar_tamano_foto(foto):
    if foto and foto.size > TAMANO_MAXIMO_FOTO:
        raise forms.ValidationError("La fotografía no puede pesar más de 5 MB.")


LADO_MAXIMO_FOTO = 1280  # píxeles
CALIDAD_WEBP = 80


def optimizar_foto(foto):
    """Reduce la fotografía a 1280 px como máximo y la guarda en WebP.

    Las fotos de celular pesan varios MB; así se guardan con unos cientos de KB
    y cargan más rápido. El límite de 5 MB se valida antes, sobre el archivo original.
    """
    if not isinstance(foto, UploadedFile):
        # Vacío, o una foto que ya estaba guardada (por ejemplo, al editar en el panel de administración).
        return foto
    foto.seek(0)
    with Image.open(foto) as original:
        imagen = ImageOps.exif_transpose(original)  # respeta la rotación del celular
        imagen.thumbnail((LADO_MAXIMO_FOTO, LADO_MAXIMO_FOTO))
        tiene_transparencia = imagen.mode in ("RGBA", "LA") or "transparency" in imagen.info
        imagen = imagen.convert("RGBA" if tiene_transparencia else "RGB")
        salida = io.BytesIO()
        imagen.save(salida, "WEBP", quality=CALIDAD_WEBP)
    nombre = os.path.splitext(os.path.basename(foto.name))[0] + ".webp"
    return ContentFile(salida.getvalue(), name=nombre)


class FiltroReportesForm(EstiloBootstrapMixin, forms.Form):
    """RF11."""

    buscar = forms.CharField(label="Buscar", required=False)
    categoria = forms.ModelChoiceField(
        CategoriaProblema.objects.filter(activa=True), label="Categoría", required=False, empty_label="Todas"
    )
    estado = forms.ChoiceField(
        choices=[("", "Todos")] + ReporteAmbiental.Estado.choices, required=False
    )
    nivel_gravedad = forms.ChoiceField(
        label="Gravedad", choices=[("", "Todas")] + ReporteAmbiental.NivelGravedad.choices, required=False
    )
    comunidad = forms.ModelChoiceField(
        Comunidad.objects.select_related("distrito__departamento"), required=False, empty_label="Todas"
    )


class ReporteForm(EstiloBootstrapMixin, forms.ModelForm):
    """RF02, RF03, RF04 y RF05: el reporte, su ubicación y la primera fotografía en un solo formulario."""

    comunidad = forms.ModelChoiceField(Comunidad.objects.select_related("distrito__departamento"))
    referencia = campo_del_modelo(
        Ubicacion,
        "referencia",
        help_text=(
            f"Mínimo {MINIMO_REFERENCIA[0]} caracteres y {MINIMO_REFERENCIA[1]} palabras. "
            "Ejemplo: frente a la escuela, a la orilla de la quebrada."
        ),
    )
    direccion = campo_del_modelo(
        Ubicacion,
        "direccion",
        label="Dirección",
        help_text=f"Opcional. Si la escribe: mínimo {MINIMO_REFERENCIA[0]} caracteres y {MINIMO_REFERENCIA[1]} palabras.",
    )
    latitud = forms.DecimalField(
        max_digits=10, decimal_places=7, min_value=LATITUD_MINIMA, max_value=LATITUD_MAXIMA, required=False,
        help_text=f"Opcional. Dentro de El Salvador: entre {LATITUD_MINIMA} y {LATITUD_MAXIMA}.",
    )
    longitud = forms.DecimalField(
        max_digits=10, decimal_places=7, min_value=LONGITUD_MINIMA, max_value=LONGITUD_MAXIMA, required=False,
        help_text=f"Opcional. Dentro de El Salvador: entre {LONGITUD_MINIMA} y {LONGITUD_MAXIMA}.",
    )
    foto = forms.ImageField(
        label="Fotografía", required=False, validators=[validar_tamano_foto], help_text="Imagen de hasta 5 MB."
    )
    # Código oculto, distinto en cada formulario nuevo. Evita el reporte duplicado por doble clic.
    token_envio = forms.UUIDField(widget=forms.HiddenInput, required=False)

    CAMPOS_UBICACION = ("comunidad", "referencia", "direccion", "latitud", "longitud")

    class Meta:
        model = ReporteAmbiental
        fields = ("categoria", "titulo", "descripcion", "fecha_incidente", "nivel_gravedad")
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "fecha_incidente": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }
        labels = {"nivel_gravedad": "Nivel de gravedad"}
        help_texts = {
            "titulo": (
                f"Mínimo {MINIMO_TITULO_REPORTE[0]} caracteres y {MINIMO_TITULO_REPORTE[1]} palabras. "
                "Ejemplo: Basura acumulada en la quebrada."
            ),
            "descripcion": (
                f"Mínimo {MINIMO_DESCRIPCION_REPORTE[0]} caracteres y {MINIMO_DESCRIPCION_REPORTE[1]} palabras. "
                "Ejemplo: Hay basura en el río desde hace una semana."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = CategoriaProblema.objects.filter(activa=True)
        # El calendario solo deja elegir desde hace ANIOS_MAXIMOS_INCIDENTE años hasta hoy.
        self.fields["fecha_incidente"].widget.attrs.update(
            min=self.instance.fecha_minima_incidente().isoformat(), max=timezone.localdate().isoformat()
        )
        self.fields["fecha_incidente"].help_text = f"Puede ser de hasta {ANIOS_MAXIMOS_INCIDENTE} años atrás."
        if self.instance.pk:
            # Al editar, la ubicación se carga desde el reporte; las fotos se agregan en el detalle.
            # Se guarda sobre el mismo reporte, así que no hace falta el código contra duplicados.
            ubicacion = self.instance.ubicacion
            for campo in self.CAMPOS_UBICACION:
                self.fields[campo].initial = getattr(ubicacion, campo)
            del self.fields["foto"]
            del self.fields["token_envio"]
        elif not self.is_bound:
            self.fields["token_envio"].initial = uuid.uuid4()

    def clean_foto(self):
        return optimizar_foto(self.cleaned_data.get("foto"))

    def clean(self):
        datos = super().clean()
        if (datos.get("latitud") is None) != (datos.get("longitud") is None):
            raise forms.ValidationError("Ingrese latitud y longitud juntas, o deje ambas vacías.")
        return datos

    @transaction.atomic
    def guardar(self, usuario):
        reporte = self.save(commit=False)
        ubicacion = reporte.ubicacion if reporte.pk else Ubicacion()
        for campo in self.CAMPOS_UBICACION:
            setattr(ubicacion, campo, self.cleaned_data[campo])
        ubicacion.save()
        reporte.ubicacion = ubicacion
        if not reporte.pk:
            reporte.usuario = usuario
            reporte.token_envio = self.cleaned_data.get("token_envio")
        reporte.save()
        if self.cleaned_data.get("foto"):
            reporte.evidencias.create(imagen=self.cleaned_data["foto"])
        return reporte


class EvidenciaForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = Evidencia
        fields = ("imagen", "descripcion")
        labels = {"imagen": "Fotografía"}

    def __init__(self, *args, maximo=MAXIMO_EVIDENCIAS_POR_REPORTE, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["imagen"].validators.append(validar_tamano_foto)
        self.fields["imagen"].help_text = f"Imagen de hasta 5 MB. Máximo {maximo} fotografías por reporte."

    def clean_imagen(self):
        return optimizar_foto(self.cleaned_data.get("imagen"))


class EvidenciaAdminForm(forms.ModelForm):
    """Fotografías subidas desde el panel de administración: mismo límite de 5 MB y misma conversión a WebP.

    No usa EstiloBootstrapMixin porque el panel tiene su propio diseño.
    """

    class Meta:
        model = Evidencia
        fields = ("imagen", "descripcion")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["imagen"].validators.append(validar_tamano_foto)

    def clean_imagen(self):
        return optimizar_foto(self.cleaned_data.get("imagen"))


class CambiarEstadoForm(EstiloBootstrapMixin, forms.Form):
    """RF09."""

    estado = forms.ChoiceField(label="Nuevo estado")
    observacion = campo_del_modelo(
        HistorialEstado,
        "observacion",
        label="Observación",
        help_text="Obligatoria si el reporte se descarta (por ejemplo: duplicado, falso o fuera de la comunidad).",
    )

    # Estado que tenía el reporte cuando se abrió la página. Si otro responsable lo cambió mientras tanto,
    # cambiar_estado() rechaza este envío y se queda el cambio que se guardó primero.
    estado_visto = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, reporte, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estado_visto"].initial = reporte.estado
        # Las opciones salen del estado que la persona estaba viendo, para que su elección se acepte aquí
        # y sea cambiar_estado() quien le explique que el reporte ya cambió.
        try:
            visto = ReporteAmbiental.Estado(self.data.get(self.add_prefix("estado_visto")))
        except ValueError:
            visto = reporte.estado
        self.fields["estado"].choices = [
            (e.value, e.label) for e in ReporteAmbiental.Estado if e in ReporteAmbiental.TRANSICIONES[visto]
        ]

    def clean(self):
        datos = super().clean()
        if datos.get("estado") == ReporteAmbiental.Estado.DESCARTADO and not datos.get("observacion", "").strip():
            self.add_error("observacion", "Indique el motivo por el que se descarta el reporte.")
        return datos


class SeguimientoForm(EstiloBootstrapMixin, forms.ModelForm):
    """RF10."""

    class Meta:
        model = Seguimiento
        fields = ("accion", "descripcion")
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3})}
        help_texts = {"accion": "Ejemplo: inspección, limpieza, notificación a la alcaldía."}


class AporteForm(EstiloBootstrapMixin, forms.Form):
    """Información adicional que el ciudadano agrega a su propio reporte."""

    descripcion = campo_del_modelo(
        Seguimiento,
        "descripcion",
        label="Información adicional",
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Por ejemplo: el problema empeoró, ahora también queman la basura, etc.",
    )


class TomarCasoForm(EstiloBootstrapMixin, forms.Form):
    """El responsable toma un caso para su institución."""

    observacion = campo_del_modelo(
        AsignacionReporte,
        "observacion",
        label="Observación",
        help_text="Opcional. Por ejemplo: se visitará el lugar esta semana.",
    )


class AsignarForm(EstiloBootstrapMixin, forms.Form):
    """Solo el administrador: asigna o reasigna el caso a una institución."""

    institucion = forms.ModelChoiceField(Institucion.objects.filter(activa=True), label="Institución")
    observacion = campo_del_modelo(AsignacionReporte, "observacion", label="Observación")
