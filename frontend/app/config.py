"""Configuration du frontend Flet — lit les variables d'environnement (.env).

Règle de robustesse : si une variable d'environnement est absente ou mal
définie sur Render (oubli, faute de frappe), on ne doit JAMAIS retomber sur
"localhost" en production — on retombe sur l'URL réelle du backend.
"""
from decouple import config

# ─── Adresse du backend en production ─────────────────────────────────────
# Valeur fixe et fiable : sert de filet de sécurité pour toutes les URLs
# dérivées ci-dessous, même si les variables d'environnement sont absentes.
BACKEND_URL = "https://cimetiere-gi2.onrender.com"

# ─── URL de l'API ──────────────────────────────────────────────────────────
# En dev local, définissez API_BASE_URL=http://localhost:8000/api dans votre
# .env. En prod, si la variable n'est pas définie sur Render, on retombe
# automatiquement sur BACKEND_URL (jamais sur localhost).
API_BASE_URL = config("API_BASE_URL", default=f"{BACKEND_URL}/api")

# ─── URL de la carte embarquée ─────────────────────────────────────────────
# Configurable indépendamment via MAP_EMBED_URL si besoin (ex: pointer la
# carte vers la prod tout en développant l'API en local). Par défaut,
# construite directement à partir de BACKEND_URL (fixe et fiable), pas en
# découpant API_BASE_URL — plus robuste si le format d'API_BASE_URL change.
MAP_EMBED_URL = config(
    "MAP_EMBED_URL",
    default=f"{BACKEND_URL}/cimetiere/carte-embed/",
)

# ─── Application ────────────────────────────────────────────────────────────
APP_TITLE = "Cimetière Municipal de Vindoulou — GI2 2026"
APP_PORT = config("FLET_PORT", default=8550, cast=int)

# ─── Palette "gothique vert sombre" ────────────────────────────────────────
# (cohérente avec le design déjà validé : dark-green + gothique)
COLOR_BG = "#0f1a14"
COLOR_SURFACE = "#182a20"
COLOR_SURFACE_LIGHT = "#22392c"
COLOR_PRIMARY = "#2d9e6f"
COLOR_PRIMARY_DARK = "#1f6b4d"
COLOR_ACCENT = "#c9a961"  # doré, touche funéraire/gothique
COLOR_TEXT = "#e8f0ea"
COLOR_TEXT_MUTED = "#9db3a4"
COLOR_DANGER = "#c0392b"
COLOR_WARNING = "#d4a017"
COLOR_SUCCESS = "#2d9e6f"
COLOR_INFO = "#3a7ca5"
COLOR_BORDER = "#2e4536"

# ─── Couleurs par statut (tous modèles confondus) ──────────────────────────
STATUS_COLORS = {
    # cemetery.Grave
    "libre": COLOR_SUCCESS,
    "occupe": COLOR_DANGER,
    "reserve": COLOR_WARNING,
    "maintenance": COLOR_TEXT_MUTED,
    # reservations.Reservation
    "en_attente": COLOR_WARNING,
    "validee": COLOR_SUCCESS,
    "refusee": COLOR_DANGER,
    "archivee": COLOR_TEXT_MUTED,
    # concessions.Concession
    "active": COLOR_SUCCESS,
    "expiree": COLOR_WARNING,
    "resiliee": COLOR_DANGER,
    # exhumations.Exhumation
    "planifie": COLOR_INFO,
    "en_cours": COLOR_WARNING,
    "termine": COLOR_SUCCESS,
    # payments.MomoTransaction
    "PENDING": COLOR_WARNING,
    "SUCCESSFUL": COLOR_SUCCESS,
    "FAILED": COLOR_DANGER,
}

# ─── Libellés des rôles utilisateurs ───────────────────────────────────────
ROLE_LABELS = {
    "admin": "Administrateur",
    "gestionnaire": "Gestionnaire",
    "agent": "Agent",
}