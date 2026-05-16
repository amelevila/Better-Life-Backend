#!/usr/bin/env bash
# deploy.sh — Ejecutar una sola vez después de desplegar el backend en AWS.
# Requiere que el .env esté configurado con las credenciales de RDS.
#
# Uso:
#   cd /ruta/al/proyecto
#   source myenv/bin/activate          # o el entorno virtual que uses
#   bash scripts/deploy.sh

set -euo pipefail

echo "==> [1/4] Instalando dependencias..."
pip install -r requirements.txt

echo "==> [2/4] Aplicando migraciones de base de datos..."
python manage.py migrate --noinput

echo "==> [3/4] Recogiendo archivos estáticos..."
python manage.py collectstatic --noinput

echo "==> [4/4] Cargando datos iniciales (ejercicios + recetas)..."
python manage.py seed_all

echo ""
echo "✔  Despliegue inicial completado."
echo "   Inicia Gunicorn con:  gunicorn better_life_backend.wsgi --config gunicorn.conf.py"
