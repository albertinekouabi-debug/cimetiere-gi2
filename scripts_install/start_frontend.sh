#!/usr/bin/env bash
# ============================================================================
# Lance le frontend Flet (mode web) en développement.
# Prérequis :
#   - avoir exécuté scripts_install/setup.sh au moins une fois
#   - le backend doit déjà être démarré (./scripts_install/start_backend.sh)
#
# Usage :
#   chmod +x scripts_install/start_frontend.sh
#   ./scripts_install/start_frontend.sh
# ============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

if [ ! -d "$FRONTEND_DIR/venv" ]; then
    echo "✗ Environnement virtuel introuvable. Exécutez d'abord : ./scripts_install/setup.sh"
    exit 1
fi

if [ ! -f "$FRONTEND_DIR/.env" ]; then
    echo "✗ frontend/.env introuvable. Exécutez d'abord : ./scripts_install/setup.sh"
    exit 1
fi

cd "$FRONTEND_DIR"
echo "➜ Démarrage du frontend sur http://localhost:8550"
echo "  Assurez-vous que le backend tourne déjà (./scripts_install/start_backend.sh)"
echo "  Arrêt : Ctrl+C"
echo ""
exec "$FRONTEND_DIR/venv/bin/python" main.py
