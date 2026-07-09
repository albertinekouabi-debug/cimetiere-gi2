import csv
import io
from typing import List, Optional
from django.http import HttpResponse
from ninja import Router, Query
from apps.accounts.auth import jwt_auth
from apps.core.permissions import require_admin
from .models import AuditLog
from .schemas import AuditLogOut

router = Router(tags=["Audit"], auth=jwt_auth)

ACTION_LABELS = {"create": "Création", "update": "Modification", "delete": "Suppression", "login": "Connexion"}


def _filtered_queryset(request, table_name: Optional[str], action: Optional[str], limit: int):
    require_admin(request)
    qs = AuditLog.objects.select_related("user").all()
    if table_name:
        qs = qs.filter(table_name=table_name)
    if action:
        qs = qs.filter(action=action)
    return qs[:limit]


@router.get("/", response=List[AuditLogOut])
def list_audit_logs(request, table_name: Optional[str] = Query(None), action: Optional[str] = Query(None), limit: int = Query(200, le=500)):
    qs = _filtered_queryset(request, table_name, action, limit)
    return [
        AuditLogOut(
            id=log.id,
            user_id=log.user_id,
            user_email=log.user.email if log.user else None,
            action=log.action,
            table_name=log.table_name,
            record_id=log.record_id,
            old_values=log.old_values,
            new_values=log.new_values,
            ip_address=log.ip_address,
            created_at=log.created_at,
        )
        for log in qs
    ]


@router.get("/export/csv")
def export_audit_csv(request, table_name: Optional[str] = Query(None), action: Optional[str] = Query(None), limit: int = Query(500, le=2000)):
    qs = _filtered_queryset(request, table_name, action, limit)
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Date/heure", "Utilisateur", "Action", "Table", "Référence", "Adresse IP"])
    for log in qs:
        writer.writerow([
            log.created_at.strftime("%d/%m/%Y %H:%M:%S"),
            log.user.email if log.user else "Système",
            ACTION_LABELS.get(log.action, log.action),
            log.table_name, log.record_id or "", log.ip_address or "",
        ])
    csv_bytes = "\ufeff" + buf.getvalue()
    response = HttpResponse(csv_bytes, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="journal_audit.csv"'
    return response
