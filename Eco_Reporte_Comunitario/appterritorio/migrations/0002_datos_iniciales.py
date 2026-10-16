from django.db import migrations


def crear_territorio(apps, schema_editor):
    Departamento = apps.get_model("appterritorio", "Departamento")
    Distrito = apps.get_model("appterritorio", "Distrito")
    Comunidad = apps.get_model("appterritorio", "Comunidad")

    chalatenango, _ = Departamento.objects.get_or_create(nombre="Chalatenango")
    san_ignacio, _ = Distrito.objects.get_or_create(nombre="San Ignacio", departamento=chalatenango)
    Comunidad.objects.get_or_create(nombre="Las Toreras", distrito=san_ignacio)


class Migration(migrations.Migration):

    dependencies = [
        ('appterritorio', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_territorio, migrations.RunPython.noop),
    ]
