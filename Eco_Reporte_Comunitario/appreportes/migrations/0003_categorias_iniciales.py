from django.db import migrations

CATEGORIAS = [
    ("Acumulación de basura", "Residuos sólidos acumulados en calles, terrenos o espacios comunitarios."),
    ("Botadero clandestino", "Sitio no autorizado donde se depositan desechos de forma recurrente."),
    ("Contaminación de río o quebrada", "Vertido de aguas residuales, basura u otros contaminantes en cuerpos de agua."),
    ("Quema de desechos", "Quema de basura u otros residuos a cielo abierto."),
    ("Daño en zonas verdes", "Tala no autorizada de árboles o deterioro de áreas verdes."),
]


def crear_categorias(apps, schema_editor):
    CategoriaProblema = apps.get_model("appreportes", "CategoriaProblema")
    for nombre, descripcion in CATEGORIAS:
        CategoriaProblema.objects.get_or_create(nombre=nombre, defaults={"descripcion": descripcion})


class Migration(migrations.Migration):

    dependencies = [
        ('appreportes', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(crear_categorias, migrations.RunPython.noop),
    ]
