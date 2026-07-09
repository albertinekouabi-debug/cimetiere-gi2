"""
Configuration Django - Gestion de Cimetière GI2 (v2)
Backend: Django + Django Ninja + PostgreSQL
"""
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Sécurité ────────────────────────────────────────────────────────────────
SECRET_KEY = config("DJANGO_SECRET_KEY")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ─── Applications ────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "ninja",
    "apps.accounts",
    "apps.cemetery",
    "apps.reservations",
    "apps.concessions",
    "apps.exhumations",
    "apps.payments",
    "apps.notifications",
    "apps.audit",
    "apps.core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.CurrentRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ─── Base de données ─────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
    }
}

# ─── Authentification ────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── JWT (utilisé par apps.accounts.auth) ────────────────────────────────────
JWT_SECRET_KEY = config("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_LIFETIME_MIN = config("JWT_ACCESS_TOKEN_LIFETIME_MIN", default=60, cast=int)
JWT_REFRESH_TOKEN_LIFETIME_DAYS = config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7, cast=int)

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# ─── MTN MoMo ─────────────────────────────────────────────────────────────────
MOMO_ENV = config("MOMO_ENV", default="sandbox")
MOMO_BASE_URL = config("MOMO_BASE_URL", default="https://sandbox.momodeveloper.mtn.com")
MOMO_SUBSCRIPTION_KEY = config("MOMO_SUBSCRIPTION_KEY", default="")
MOMO_API_USER = config("MOMO_API_USER", default="")
MOMO_API_KEY = config("MOMO_API_KEY", default="")
MOMO_TARGET_ENVIRONMENT = config("MOMO_TARGET_ENVIRONMENT", default="sandbox")
MOMO_CALLBACK_HOST = config("MOMO_CALLBACK_HOST", default="")

# ─── Google Maps (carte interactive du cimetière) ─────────────────────────────
GOOGLE_MAPS_API_KEY = config("GOOGLE_MAPS_API_KEY", default="")

# Coordonnées exactes du Cimetière Municipal de Vindoulou, Pointe-Noire.
CEMETERY_CENTER_LAT = config("CEMETERY_CENTER_LAT", default=-4.7333, cast=float)
CEMETERY_CENTER_LNG = config("CEMETERY_CENTER_LNG", default=11.9167, cast=float)

# Points de repère approximatifs délimitant le site (entrée + limites NE/SO).
# Ces 3 points ne forment pas un polygone fermé au sens strict (données de
# terrain limitées) : ils sont reliés pour donner un contour indicatif du
# site sur la carte, pas une limite cadastrale exacte.
CEMETERY_BOUNDARY_POINTS = [
    {"lat": -4.7345, "lng": 11.9155, "label": "Entrée principale"},
    {"lat": -4.7312, "lng": 11.9185, "label": "Limite Nord-Est"},
    {"lat": -4.7358, "lng": 11.9142, "label": "Limite Sud-Ouest"},
]

# ─── Internationalisation ─────────────────────────────────────────────────────
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Brazzaville"
USE_I18N = True
USE_TZ = True

# ─── Fichiers statiques ────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Logging ────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "cimetiere": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}

# ─── Ninja ────────────────────────────────────────────────────────────────────
NINJA_PAGINATION_PER_PAGE = 20
