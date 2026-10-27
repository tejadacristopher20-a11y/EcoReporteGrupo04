from django import forms
from django.db import transaction

from Eco_Reporte_Comunitario.formularios import EstiloBootstrapMixin

from appinstituciones.models import Institucion
from appterritorio.models import Comunidad, Ubicacion

from .models import CategoriaProblema, Evidencia, ReporteAmbiental, Seguimiento

TAMANO_MAXIMO_FOTO = 5 * 1024 * 1024  # 5 MB


def validar_tamano_foto(foto):
    if foto and foto.size > TAMANO_MAXIMO_FOTO:
        raise forms.ValidationError("La fotografía no puede pesar más de 5 MB.")


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
    referencia = forms.CharField(
        max_length=200, help_text="Ejemplo: frente a la escuela, a la orilla de la quebrada."
    )
    direccion = forms.CharField(label="Dirección", max_length=250, required=False)
    latitud = forms.DecimalField(max_digits=10, decimal_places=7, min_value=-90, max_value=90, required=False)
    longitud = forms.DecimalField(max_digits=10, decimal_places=7, min_value=-180, max_value=180, required=False)
    foto = forms.ImageField(
        label="Fotografía", required=False, validators=[validar_tamano_foto], help_text="Imagen de hasta 5 MB."
    )

    CAMPOS_UBICACION = ("comunidad", "referencia", "direccion", "latitud", "longitud")

    class Meta:
        model = ReporteAmbiental
        fields = ("categoria", "titulo", "descripcion", "fecha_incidente", "nivel_gravedad")
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "fecha_incidente": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }
        labels = {"nivel_gravedad": "Nivel de gravedad"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = CategoriaProblema.objects.filter(activa=True)
        if self.instance.pk:
            # Al editar, la ubicación se carga desde el reporte; las fotos se agregan en el detalle.
            ubicacion = self.instance.ubicacion
            for campo in self.CAMPOS_UBICACION:
                self.fields[campo].initial = getattr(ubicacion, campo)
            del self.fields["foto"]

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
        reporte.save()
        if self.cleaned_data.get("foto"):
            reporte.evidencias.create(imagen=self.cleaned_data["foto"])
        return reporte


class EvidenciaForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = Evidencia
        fields = ("imagen", "descripcion")
        labels = {"imagen": "Fotografía"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["imagen"].validators.append(validar_tamano_foto)


class CambiarEstadoForm(EstiloBootstrapMixin, forms.Form):
    """RF09."""

    estado = forms.ChoiceField(label="Nuevo estado")
    observacion = forms.CharField(
        label="Observación",
        max_length=300,
        required=False,
        help_text="Obligatoria si el reporte se descarta (por ejemplo: duplicado, falso o fuera de la comunidad).",
    )

    def __init__(self, *args, reporte, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estado"].choices = [(e.value, e.label) for e in reporte.estados_siguientes()]

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

    descripcion = forms.CharField(
        label="Información adicional",
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Por ejemplo: el problema empeoró, ahora también queman la basura, etc.",
    )


class AsignarForm(EstiloBootstrapMixin, forms.Form):
    institucion = forms.ModelChoiceField(Institucion.objects.filter(activa=True), label="Institución")
    observacion = forms.CharField(label="Observación", max_length=300, required=False)
