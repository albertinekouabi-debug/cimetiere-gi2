"""
Authentification JWT pour l'API Django Ninja.
Remplace l'auth Supabase (auth.users + session) par un flux JWT classique
access + refresh, avec un HttpBearer custom pour Ninja.
"""
import jwt
import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from django.conf import settings
from ninja.security import HttpBearer
from ninja.errors import HttpError

from .models import User


def _now():
    return datetime.now(dt_timezone.utc)


def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "type": "access",
        "iat": _now(),
        "exp": _now() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME_MIN),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "type": "refresh",
        "iat": _now(),
        "exp": _now() + timedelta(days=settings.JWT_REFRESH_TOKEN_LIFETIME_DAYS),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HttpError(401, "Jeton expiré, veuillez vous reconnecter.")
    except jwt.InvalidTokenError:
        raise HttpError(401, "Jeton invalide.")


class JWTAuth(HttpBearer):
    """Auth Bearer pour les endpoints protégés (personnel authentifié)."""

    def authenticate(self, request, token):
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HttpError(401, "Type de jeton invalide.")
        try:
            user = User.objects.get(id=payload["sub"])
        except User.DoesNotExist:
            raise HttpError(401, "Utilisateur introuvable.")
        if not user.is_active:
            raise HttpError(403, "Compte désactivé. Contactez un administrateur.")
        return user


jwt_auth = JWTAuth()
