#!/bin/bash

# Ejecutar migraciones
python manage.py migrate --noinput

# Recolectar archivos estáticos
python manage.py collectstatic --noinput --clear

# Iniciar Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
