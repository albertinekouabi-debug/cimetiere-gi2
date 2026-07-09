from typing import List
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from apps.core.permissions import require_admin
from apps.audit.utils import log_action
from .auth import jwt_auth, create_access_token, create_refresh_token, decode_token
from .models import User
from .schemas import (
    LoginIn, LoginOut, TokenOut, RefreshIn, ProfileOut,
    UserCreateIn, UserUpdateIn, PasswordChangeIn, AdminPasswordResetIn,
)

router = Router(tags=["Comptes"])


def _profile_out(user: User) -> ProfileOut:
    return ProfileOut(
        id=user.id, email=user.email, full_name=user.full_name, role=user.role,
        phone=user.phone, is_active=user.is_active,
        created_at=user.created_at, updated_at=user.updated_at,
    )


@router.post("/auth/login", response=LoginOut, auth=None)
def login(request, payload: LoginIn):
    user = authenticate(request, username=payload.email, password=payload.password)
    if user is None:
        # authenticate() nécessite USERNAME_FIELD=email correctement configuré ;
        # on retente une résolution manuelle par email pour robustesse.
        try:
            candidate = User.objects.get(email__iexact=payload.email)
            if candidate.check_password(payload.password):
                user = candidate
        except User.DoesNotExist:
            user = None
    if user is None:
        raise HttpError(401, "Email ou mot de passe incorrect.")
    if not user.is_active:
        raise HttpError(403, "Compte désactivé. Contactez un administrateur.")

    log_action(user, "login", "auth", record_id=user.id)
    return LoginOut(
        tokens=TokenOut(access_token=create_access_token(user), refresh_token=create_refresh_token(user)),
        profile=_profile_out(user),
    )


@router.post("/auth/refresh", response=TokenOut, auth=None)
def refresh_token(request, payload: RefreshIn):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise HttpError(401, "Jeton de rafraîchissement invalide.")
    user = get_object_or_404(User, id=data["sub"])
    if not user.is_active:
        raise HttpError(403, "Compte désactivé.")
    return TokenOut(access_token=create_access_token(user), refresh_token=create_refresh_token(user))


@router.get("/auth/me", response=ProfileOut, auth=jwt_auth)
def me(request):
    return _profile_out(request.auth)


@router.post("/auth/change-password", auth=jwt_auth)
def change_password(request, payload: PasswordChangeIn):
    user: User = request.auth
    if not user.check_password(payload.old_password):
        raise HttpError(400, "Ancien mot de passe incorrect.")
    if len(payload.new_password) < 8:
        raise HttpError(400, "Le nouveau mot de passe doit contenir au moins 8 caractères.")
    user.set_password(payload.new_password)
    user.save(update_fields=["password"])
    log_action(user, "update", "profiles", record_id=user.id, new_values={"action": "password_change"})
    return {"detail": "Mot de passe mis à jour."}


# ─── Gestion des utilisateurs (admin uniquement) ─────────────────────────────

@router.get("/users", response=List[ProfileOut], auth=jwt_auth)
def list_users(request):
    require_admin(request)
    return [_profile_out(u) for u in User.objects.all()]


@router.post("/users", response=ProfileOut, auth=jwt_auth)
def create_user(request, payload: UserCreateIn):
    require_admin(request)
    if User.objects.filter(email__iexact=payload.email).exists():
        raise HttpError(400, "Un utilisateur avec cet email existe déjà.")
    if len(payload.password) < 8:
        raise HttpError(400, "Le mot de passe doit contenir au moins 8 caractères.")
    user = User.objects.create_user(
        username=payload.email,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        phone=payload.phone,
    )
    log_action(request.auth, "create", "profiles", record_id=user.id, new_values={"email": user.email, "role": user.role})
    return _profile_out(user)


@router.put("/users/{user_id}", response=ProfileOut, auth=jwt_auth)
def update_user(request, user_id: str, payload: UserUpdateIn):
    require_admin(request)
    user = get_object_or_404(User, id=user_id)
    old = {"full_name": user.full_name, "role": user.role, "is_active": user.is_active}
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(user, field, value)
    user.save()
    log_action(request.auth, "update", "profiles", record_id=user.id, old_values=old, new_values=payload.dict(exclude_unset=True))
    return _profile_out(user)


@router.post("/users/{user_id}/reset-password", auth=jwt_auth)
def admin_reset_password(request, user_id: str, payload: AdminPasswordResetIn):
    """Permet à un administrateur de réinitialiser le mot de passe de
    n'importe quel utilisateur (sans connaître l'ancien), par exemple en cas
    d'oubli. L'action est tracée dans le journal d'audit."""
    require_admin(request)
    if len(payload.new_password) < 8:
        raise HttpError(400, "Le nouveau mot de passe doit contenir au moins 8 caractères.")
    user = get_object_or_404(User, id=user_id)
    user.set_password(payload.new_password)
    user.save(update_fields=["password"])
    log_action(request.auth, "update", "profiles", record_id=user.id, new_values={"action": "admin_password_reset", "target_email": user.email})
    return {"detail": f"Mot de passe de {user.email} réinitialisé."}


@router.delete("/users/{user_id}", auth=jwt_auth)
def delete_user(request, user_id: str):
    require_admin(request)
    if str(request.auth.id) == str(user_id):
        raise HttpError(400, "Vous ne pouvez pas supprimer votre propre compte.")
    user = get_object_or_404(User, id=user_id)
    log_action(request.auth, "delete", "profiles", record_id=user.id, old_values={"email": user.email})
    user.delete()
    return {"detail": "Utilisateur supprimé."}
