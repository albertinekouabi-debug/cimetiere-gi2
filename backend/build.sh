#!/usr/bin/env bash
set -o errexit

echo "Installation des dependances..."
pip install -r requirements.txt

echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "Application des migrations..."
python manage.py migrate

echo "Build termine."