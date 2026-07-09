#!/usr/bin/env bash
# ============================================================================
# Installation complète — Gestion de Cimetière GI2 2026 v2
# À exécuter UNE SEULE FOIS, depuis la racine du projet (cimetiere_gi2/).
#
# Usage :
#   chmod +x scripts_install/setup.sh
#   ./scripts_install/setup.sh
# ============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${BLUE}➜${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
fail()  { echo -e "${RED}✗${NC} $1"; exit 1; }

echo "============================================================"
echo " Installation — Gestion de Cimetière GI2 2026 v2"
echo "============================================================"

# ─── 1. Vérification des prérequis ─────────────────────────────────────────
info "Vérification de Python 3..."
command -v python3 >/dev/null 2>&1 || fail "Python 3 est requis mais introuvable. Installez-le puis relancez ce script."
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
ok "Python $PYTHON_VERSION détecté."

info "Vérification de PostgreSQL (client psql)..."
if command -v psql >/dev/null 2>&1; then
    ok "Client PostgreSQL détecté."
else
    warn "Le client 'psql' n'a pas été trouvé. Assurez-vous qu'un serveur PostgreSQL est accessible (local ou distant) avant de continuer."
fi

# ─── 2. Backend ─────────────────────────────────────────────────────────────
echo ""
echo "------------------------------------------------------------"
echo " BACKEND (Django + Django Ninja + PostgreSQL)"
echo "------------------------------------------------------------"
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    info "Création de l'environnement virtuel Python (backend/venv)..."
    python3 -m venv venv
    ok "Environnement virtuel créé."
else
    ok "Environnement virtuel déjà présent, réutilisation."
fi

info "Installation des dépendances backend..."
"$BACKEND_DIR/venv/bin/pip" install --upgrade pip -q
"$BACKEND_DIR/venv/bin/pip" install -r requirements.txt -q
ok "Dépendances backend installées."

if [ ! -f ".env" ]; then
    cp .env.example .env
    warn "Fichier backend/.env créé à partir de .env.example."
    warn "  -> OUVREZ backend/.env et renseignez au minimum :"
    warn "     DJANGO_SECRET_KEY, JWT_SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT"
    warn "  -> Optionnel mais recommandé : GOOGLE_MAPS_API_KEY, MOMO_*"
    NEEDS_ENV_EDIT=1
else
    ok "Fichier backend/.env déjà présent, non modifié."
    NEEDS_ENV_EDIT=0
fi

if [ "$NEEDS_ENV_EDIT" -eq 1 ]; then
    echo ""
    read -rp "Avez-vous fini d'éditer backend/.env avec vos vraies valeurs ? [o/N] " REPLY
    if [[ ! "$REPLY" =~ ^[oOyY]$ ]]; then
        warn "Installation interrompue. Éditez backend/.env puis relancez ce script."
        exit 0
    fi
fi

info "Application des migrations de base de données..."
if "$BACKEND_DIR/venv/bin/python" manage.py migrate; then
    ok "Migrations appliquées avec succès."
else
    fail "Échec des migrations. Vérifiez la configuration PostgreSQL dans backend/.env (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT), puis relancez ce script."
fi

echo ""
info "Création du premier compte administrateur."
read -rp "  Email de l'administrateur : " ADMIN_EMAIL
read -rsp "  Mot de passe (8+ caractères) : " ADMIN_PASSWORD
echo ""
read -rp "  Nom complet : " ADMIN_NAME

if "$BACKEND_DIR/venv/bin/python" manage.py bootstrap_admin --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD" --full-name "$ADMIN_NAME"; then
    ok "Compte administrateur créé : $ADMIN_EMAIL"
else
    warn "La création de l'admin a échoué (existe peut-être déjà). Vous pourrez réessayer plus tard avec :"
    warn "  backend/venv/bin/python backend/manage.py bootstrap_admin --email ... --password ... --full-name ..."
fi

info "Collecte des fichiers statiques..."
"$BACKEND_DIR/venv/bin/python" manage.py collectstatic --noinput -q || warn "collectstatic a échoué (sans gravité en développement)."
ok "Backend prêt."

# ─── 3. Frontend ────────────────────────────────────────────────────────────
echo ""
echo "------------------------------------------------------------"
echo " FRONTEND (Flet — mode web)"
echo "------------------------------------------------------------"
cd "$FRONTEND_DIR"

if [ ! -d "venv" ]; then
    info "Création de l'environnement virtuel Python (frontend/venv)..."
    python3 -m venv venv
    ok "Environnement virtuel créé."
else
    ok "Environnement virtuel déjà présent, réutilisation."
fi

info "Installation des dépendances frontend..."
"$FRONTEND_DIR/venv/bin/pip" install --upgrade pip -q
"$FRONTEND_DIR/venv/bin/pip" install -r requirements.txt -q
ok "Dépendances frontend installées."

if [ ! -f ".env" ]; then
    cp .env.example .env
    ok "Fichier frontend/.env créé (valeurs par défaut : API sur http://localhost:8000/api, port 8550)."
else
    ok "Fichier frontend/.env déjà présent, non modifié."
fi

echo ""
echo "============================================================"
ok "INSTALLATION TERMINÉE."
echo "============================================================"
echo ""
echo "Pour lancer l'application, utilisez (dans deux terminaux séparés) :"
echo ""
echo "  Terminal 1 (backend)  : ./scripts_install/start_backend.sh"
echo "  Terminal 2 (frontend) : ./scripts_install/start_frontend.sh"
echo ""
echo "Puis ouvrez votre navigateur sur : http://localhost:8550"
echo ""
