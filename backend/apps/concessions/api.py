from typing import List
from dateutil.relativedelta import relativedelta
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from ninja import Router
from ninja.errors import HttpError

from apps.accounts.auth import jwt_auth
from apps.core.permissions import require_staff, require_manager, require_admin
from apps.audit.utils import log_action
from apps.cemetery.models import Grave, GraveStatus
from .models import Concession, ConcessionDuration, ConcessionStatus, DUREE_ANNEES
from .schemas import ConcessionIn, ConcessionOut, ConcessionRenewIn

router = Router(tags=["Concessions"], auth=jwt_auth)


def _compute_date_fin(date_debut, duree):
    if duree == ConcessionDuration.PERPETUELLE:
        return None
    annees = DUREE_ANNEES.get(duree)
    if not annees:
        raise HttpError(400, "Durée de concession invalide.")
    return date_debut + relativedelta(years=annees)


def _out(c: Concession) -> ConcessionOut:
    montant_paye = c.paiements.aggregate(total=Sum("montant"))["total"] or 0
    return ConcessionOut(
        id=c.id, grave_id=c.grave_id, grave_numero=c.grave.numero if c.grave_id else None,
        reservation_id=c.reservation_id, famille_nom=c.famille_nom, famille_contact=c.famille_contact,
        famille_email=c.famille_email, duree=c.duree, date_debut=c.date_debut, date_fin=c.date_fin,
        montant_total=float(c.montant_total), montant_paye=float(montant_paye), status=c.status,
        notes=c.notes, created_at=c.created_at, updated_at=c.updated_at,
    )


@router.get("/", response=List[ConcessionOut])
def list_concessions(request):
    require_staff(request)
    return [_out(c) for c in Concession.objects.select_related("grave").all()]


@router.post("/", response=ConcessionOut)
def create_concession(request, payload: ConcessionIn):
    require_manager(request)
    grave = get_object_or_404(Grave, id=payload.grave_id)
    date_fin = _compute_date_fin(payload.date_debut, payload.duree)
    concession = Concession.objects.create(
        grave=grave, reservation_id=payload.reservation_id, famille_nom=payload.famille_nom,
        famille_contact=payload.famille_contact, famille_email=payload.famille_email,
        duree=payload.duree, date_debut=payload.date_debut, date_fin=date_fin,
        montant_total=payload.montant_total, notes=payload.notes,
    )
    grave.status = GraveStatus.OCCUPE
    grave.save(update_fields=["status", "updated_at"])
    log_action(request.auth, "create", "concessions", record_id=concession.id, new_values={"grave": grave.numero, "famille": concession.famille_nom})
    return _out(concession)


@router.post("/{concession_id}/renew", response=ConcessionOut)
def renew_concession(request, concession_id: str, payload: ConcessionRenewIn):
    require_manager(request)
    concession = get_object_or_404(Concession, id=concession_id)
    base_date = concession.date_fin if concession.date_fin else concession.date_debut
    new_date_fin = _compute_date_fin(base_date, payload.nouvelle_duree)
    old = {"duree": concession.duree, "date_fin": str(concession.date_fin)}
    concession.duree = payload.nouvelle_duree
    concession.date_fin = new_date_fin
    concession.montant_total = float(concession.montant_total) + payload.montant_supplementaire
    concession.status = ConcessionStatus.ACTIVE
    concession.save()
    log_action(request.auth, "update", "concessions", record_id=concession.id, old_values=old, new_values={"action": "renew", "duree": concession.duree})
    return _out(concession)


@router.put("/{concession_id}", response=ConcessionOut)
def update_concession(request, concession_id: str, payload: ConcessionIn):
    require_manager(request)
    concession = get_object_or_404(Concession, id=concession_id)
    old = {"famille_nom": concession.famille_nom, "montant_total": float(concession.montant_total)}
    concession.famille_nom = payload.famille_nom
    concession.famille_contact = payload.famille_contact
    concession.famille_email = payload.famille_email
    concession.notes = payload.notes
    concession.montant_total = payload.montant_total
    concession.save()
    log_action(request.auth, "update", "concessions", record_id=concession.id, old_values=old)
    return _out(concession)


@router.delete("/{concession_id}")
def delete_concession(request, concession_id: str):
    require_admin(request)
    concession = get_object_or_404(Concession, id=concession_id)
    log_action(request.auth, "delete", "concessions", record_id=concession.id, old_values={"famille": concession.famille_nom})
    concession.delete()
    return {"detail": "Concession supprimée."}
