from .models import AuditLog
from .middleware import get_current_request, get_client_ip


def log_action(user, action: str, table_name: str, record_id=None, old_values=None, new_values=None):
    """Écrit une entrée d'audit. Ne doit jamais lever d'exception bloquante
    pour l'action métier en cours (best-effort)."""
    try:
        request = get_current_request()
        AuditLog.objects.create(
            user=user if (user and getattr(user, "is_authenticated", False)) else None,
            action=action,
            table_name=table_name,
            record_id=str(record_id) if record_id is not None else None,
            old_values=old_values,
            new_values=new_values,
            ip_address=get_client_ip(request),
        )
    except Exception:
        import logging
        logging.getLogger("cimetiere").exception("Échec de l'écriture du journal d'audit")
