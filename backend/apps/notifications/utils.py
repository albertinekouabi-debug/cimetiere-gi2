"""Utilitaires pour créer des notifications internes suite à des événements
métier (nouvelle réservation, paiement reçu, statut changé, etc.)."""
import logging
from .models import Notification

logger = logging.getLogger("cimetiere")


def notify_user(user, notif_type: str, titre: str, message: str, reference_id=None):
    """Crée une notification pour un utilisateur précis. Best-effort : ne
    doit jamais interrompre l'action métier en cours."""
    if user is None:
        return
    try:
        Notification.objects.create(
            user=user, type=notif_type, titre=titre, message=message,
            reference_id=str(reference_id) if reference_id is not None else None,
        )
    except Exception:
        logger.exception("Échec de création de notification")


def notify_roles(roles: set, notif_type: str, titre: str, message: str, reference_id=None, exclude_user=None):
    """Crée une notification pour tous les utilisateurs actifs ayant l'un des
    rôles donnés (ex: {"admin", "gestionnaire"}), en excluant éventuellement
    l'auteur de l'action pour ne pas se notifier soi-même."""
    from apps.accounts.models import User
    try:
        qs = User.objects.filter(role__in=roles, is_active=True)
        if exclude_user is not None:
            qs = qs.exclude(id=exclude_user.id)
        notifications = [
            Notification(
                user=u, type=notif_type, titre=titre, message=message,
                reference_id=str(reference_id) if reference_id is not None else None,
            )
            for u in qs
        ]
        Notification.objects.bulk_create(notifications)
    except Exception:
        logger.exception("Échec de création des notifications de rôle")
