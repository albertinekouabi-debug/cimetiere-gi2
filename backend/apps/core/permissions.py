"""
Permissions par rôle - équivalent applicatif des policies RLS de Supabase.
Rôles: admin > gestionnaire > agent (staff). Le rôle 'public' n'existe pas
côté backend: les endpoints publics sont simplement non authentifiés.
"""
from ninja.errors import HttpError

ROLE_ADMIN = "admin"
ROLE_GESTIONNAIRE = "gestionnaire"
ROLE_AGENT = "agent"

STAFF_ROLES = {ROLE_ADMIN, ROLE_GESTIONNAIRE, ROLE_AGENT}
MANAGER_ROLES = {ROLE_ADMIN, ROLE_GESTIONNAIRE}


def is_staff(user) -> bool:
    return bool(user and user.is_authenticated and user.role in STAFF_ROLES and user.is_active)


def is_manager(user) -> bool:
    return bool(user and user.is_authenticated and user.role in MANAGER_ROLES and user.is_active)


def is_admin(user) -> bool:
    return bool(user and user.is_authenticated and user.role == ROLE_ADMIN and user.is_active)


def require_staff(request):
    if not is_staff(request.auth):
        raise HttpError(403, "Accès réservé au personnel (agent, gestionnaire, admin).")


def require_manager(request):
    if not is_manager(request.auth):
        raise HttpError(403, "Accès réservé aux gestionnaires et administrateurs.")


def require_admin(request):
    if not is_admin(request.auth):
        raise HttpError(403, "Accès réservé aux administrateurs.")
