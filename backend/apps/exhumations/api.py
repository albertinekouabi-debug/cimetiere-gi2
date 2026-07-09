from typing import List
from django.utils import timezone
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from apps.accounts.auth import jwt_auth
from apps.core.permissions import require_staff, require_manager, require_admin
from apps.audit.utils import log_action
from apps.notifications.utils import notify_user
from apps.cemetery.models import Grave, GraveStatus
from .models import Exhumation, ExhumationStatus
from .schemas import ExhumationIn, ExhumationOut, ExhumationStatusIn

router = Router(tags=["Exhumations"], auth=jwt_auth)


def _out(e: Exhumation) -> ExhumationOut:
    return ExhumationOut(
        id=e.id, grave_id=e.grave_id, grave_numero=e.grave.numero if e.grave_id else None,
        concession_id=e.concession_id, status=e.status, date_planifiee=e.date_planifiee,
        date_realisation=e.date_realisation, motif=e.motif, notes=e.notes,
        created_at=e.created_at, updated_at=e.updated_at,
    )


@router.get("/", response=List[ExhumationOut])
def list_exhumations(request):
    require_staff(request)
    return [_out(e) for e in Exhumation.objects.select_related("grave").all()]


@router.post("/", response=ExhumationOut)
def create_exhumation(request, payload: ExhumationIn):
    require_staff(request)
    grave = get_object_or_404(Grave, id=payload.grave_id)
    exhumation = Exhumation.objects.create(
        grave=grave, concession_id=payload.concession_id, date_planifiee=payload.date_planifiee,
        motif=payload.motif, notes=payload.notes, created_by=request.auth,
    )
    log_action(request.auth, "create", "exhumations", record_id=exhumation.id, new_values={"grave": grave.numero})
    return _out(exhumation)


@router.post("/{exhumation_id}/status", response=ExhumationOut)
def change_status(request, exhumation_id: str, payload: ExhumationStatusIn):
    require_manager(request)
    if payload.status not in ExhumationStatus.values:
        raise HttpError(400, "Statut d'exhumation invalide.")
    exhumation = get_object_or_404(Exhumation, id=exhumation_id)
    old_status = exhumation.status
    exhumation.status = payload.status
    if payload.status == ExhumationStatus.TERMINE:
        exhumation.date_realisation = payload.date_realisation or timezone.now().date()
        grave = exhumation.grave
        grave.status = GraveStatus.LIBRE
        grave.save(update_fields=["status", "updated_at"])
    exhumation.save()
    log_action(request.auth, "update", "exhumations", record_id=exhumation.id, old_values={"status": old_status}, new_values={"status": exhumation.status})
    if payload.status == ExhumationStatus.TERMINE and exhumation.created_by_id and exhumation.created_by_id != request.auth.id:
        notify_user(
            exhumation.created_by, "systeme", "Exhumation terminée",
            f"L'exhumation du caveau {exhumation.grave.numero} est terminée. Le caveau est de nouveau libre.",
            reference_id=exhumation.id,
        )
    return _out(exhumation)


@router.delete("/{exhumation_id}")
def delete_exhumation(request, exhumation_id: str):
    require_admin(request)
    exhumation = get_object_or_404(Exhumation, id=exhumation_id)
    log_action(request.auth, "delete", "exhumations", record_id=exhumation.id)
    exhumation.delete()
    return {"detail": "Exhumation supprimée."}
