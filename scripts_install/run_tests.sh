#!/usr/bin/env bash
# ============================================================================
# Lance la suite de tests de régression (backend + frontend) contre un
# backend de développement démarré temporairement pour l'occasion.
# Utile pour vérifier l'installation ou après une modification du code.
#
# Usage :
#   chmod +x scripts_install/run_tests.sh
#   ./scripts_install/run_tests.sh
# ============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

if [ ! -d "$BACKEND_DIR/venv" ] || [ ! -d "$FRONTEND_DIR/venv" ]; then
    echo "✗ Installation incomplète. Exécutez d'abord : ./scripts_install/setup.sh"
    exit 1
fi

echo "➜ Démarrage temporaire du backend pour les tests..."
cd "$BACKEND_DIR"
"$BACKEND_DIR/venv/bin/python" manage.py runserver 127.0.0.1:8123 --noreload > /tmp/cimetiere_test_server.log 2>&1 &
SERVER_PID=$!
sleep 3

cleanup() {
    echo "➜ Arrêt du serveur de test (PID $SERVER_PID)..."
    kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo ""
echo "=== Régression API backend ==="
"$BACKEND_DIR/venv/bin/python" scripts/regression_test.py || {
    echo "✗ Des tests backend ont échoué. Voir /tmp/cimetiere_test_server.log pour les logs serveur."
    exit 1
}

echo ""
echo "=== Tests des pages frontend ==="
cd "$FRONTEND_DIR"
API_BASE_URL="http://127.0.0.1:8123/api" "$FRONTEND_DIR/venv/bin/python" scripts/test_pages.py || {
    echo "✗ Des tests frontend ont échoué."
    exit 1
}

echo ""
echo "✓ TOUS LES TESTS SONT PASSÉS."
