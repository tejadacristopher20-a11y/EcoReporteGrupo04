#!/usr/bin/env bash
# Script de construcción para Render (Build Command: bash build.sh).
# Va en la raíz del repositorio, junto a requirements.txt y .python-version.

# Detener el despliegue si ocurre algún error
set -o errexit

# Instalar las dependencias
pip install -r requirements.txt

# El proyecto de Django (manage.py) está en la carpeta Eco_Reporte_Comunitario
cd Eco_Reporte_Comunitario

# Preparar los archivos estáticos
python manage.py collectstatic --no-input

# Aplicar las migraciones de Django
python manage.py migrate --noinput

# Crear el administrador la primera vez, si en Render se definieron las variables
# DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL y DJANGO_SUPERUSER_PASSWORD.
# El sistema permite un solo administrador: en los despliegues siguientes ya existe y se continúa normalmente.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser --noinput || echo "El administrador ya existe; se continúa con el despliegue."
fi
