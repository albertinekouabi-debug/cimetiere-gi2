#!/usr/bin/env bash
# ============================================================================
# Lance le backend Django (API) en mode développement.
# Prérequis : avoir exécuté scripts_install/setup.sh au moins une fois.
#
# Usage :
#   chmod +x scripts_install/start_backend.sh
#   ./scripts_install/start_backend.sh
# ============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "✗ Environnement virtuel introuvable. Exécutez d'abord : ./scripts_install/setup.sh"
    exit 1
fi

if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "✗ backend/.env introuvable. Exécutez d'abord : ./scripts_install/setup.sh"
    exit 1
fi

cd "$BACKEND_DIR"
echo "➜ Démarrage du backend sur http://localhost:8000 (API sur /api, admin Django sur /admin)"
echo "  Arrêt : Ctrl+C"
echo ""
exec "$BACKEND_DIR/venv/bin/python" manage.py runserver 0.0.0.0:8000
