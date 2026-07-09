"""Configuration du frontend Flet — lit les variables d'environnement (.env)."""
from decouple import config

API_BASE_URL = config("API_BASE_URL", default="http://localhost:8000/api")
API_ORIGIN = API_BASE_URL.rsplit("/api", 1)[0]  # ex: http://localhost:8000
MAP_EMBED_URL = f"{API_ORIGIN}/cimetiere/carte-embed/"
APP_TITLE = "Cimetière Municipal de Vindoulou — GI2 2026"
APP_PORT = config("FLET_PORT", default=8550, cast=int)

# Palette "gothique vert sombre" (cohérente avec le design déjà validé sur le
# projet précédent : dark-green + gothique).
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

STATUS_COLORS = {
    "libre": COLOR_SUCCESS,
    "occupe": COLOR_DANGER,
    "reserve": COLOR_WARNING,
    "maintenance": COLOR_TEXT_MUTED,
    "en_attente": COLOR_WARNING,
    "validee": COLOR_SUCCESS,
    "refusee": COLOR_DANGER,
    "archivee": COLOR_TEXT_MUTED,
    "active": COLOR_SUCCESS,
    "expiree": COLOR_WARNING,
    "resiliee": COLOR_DANGER,
    "planifie": COLOR_INFO,
    "en_cours": COLOR_WARNING,
    "termine": COLOR_SUCCESS,
    "PENDING": COLOR_WARNING,
    "SUCCESSFUL": COLOR_SUCCESS,
    "FAILED": COLOR_DANGER,
}

ROLE_LABELS = {"admin": "Administrateur", "gestionnaire": "Gestionnaire", "agent": "Agent"}
