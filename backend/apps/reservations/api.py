from typing import List
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from ninja import Router
from ninja.errors import HttpError

from apps.accounts.auth import jwt_auth
from apps.core.permissions import require_staff, require_manager, require_admin
from apps.audit.utils import log_action
from apps.notifications.utils import notify_roles, notify_user
from apps.cemetery.models import Grave, GraveStatus
from .models import Reservation, ReservationStatus
from .schemas import ReservationIn, ReservationOut, ReservationValidateIn, ReservationStatsOut

router = Router(tags=["Réservations"], auth=jwt_auth)


def _out(r: Reservation) -> ReservationOut:
    return ReservationOut(
        id=r.id, grave_id=r.grave_id, grave_numero=r.grave.numero if r.grave_id else None,
        defunt_nom=r.defunt_nom, defunt_prenom=r.defunt_prenom, defunt_date_deces=r.defunt_date_deces,
        famille_nom=r.famille_nom, famille_contact=r.famille_contact, famille_email=r.famille_email,
        status=r.status, created_by_nom=r.created_by.full_name if r.created_by_id else None,
        validated_by_nom=r.validated_by.full_name if r.validated_by_id else None,
        validated_at=r.validated_at, notes=r.notes, created_at=r.created_at, updated_at=r.updated_at,
    )


@router.get("/", response=List[ReservationOut])
def list_reservations(request):
    require_staff(request)
    qs = Reservation.objects.select_related("grave", "created_by", "validated_by").all()
    return [_out(r) for r in qs]


@router.post("/", response=ReservationOut)
def create_reservation(request, payload: ReservationIn):
    require_staff(request)
    grave = get_object_or_404(Grave, id=payload.grave_id)
    if grave.status not in (GraveStatus.LIBRE,):
        raise HttpError(400, "Ce caveau n'est pas disponible pour une réservation.")
    reservation = Reservation.objects.create(
        grave=grave, defunt_nom=payload.defunt_nom, defunt_prenom=payload.defunt_prenom,
        defunt_date_deces=payload.defunt_date_deces, famille_nom=payload.famille_nom,
        famille_contact=payload.famille_contact, famille_email=payload.famille_email,
        notes=payload.notes, created_by=request.auth,
    )
    log_action(request.auth, "create", "reservations", record_id=reservation.id, new_values={"grave": grave.numero, "famille": reservation.famille_nom})
    notify_roles(
        {"admin", "gestionnaire"}, "reservation", "Nouvelle réservation en attente",
        f"{reservation.famille_nom} — caveau {grave.numero} — en attente de validation.",
        reference_id=reservation.id, exclude_user=request.auth,
    )
    return _out(reservation)


@router.post("/{reservation_id}/validate", response=ReservationOut)
def validate_reservation(request, reservation_id: str, payload: ReservationValidateIn):
    require_manager(request)
    if payload.status not in (ReservationStatus.VALIDEE, ReservationStatus.REFUSEE):
        raise HttpError(400, "Statut invalide : utilisez 'validee' ou 'refusee'.")
    reservation = get_object_or_404(Reservation, id=reservation_id)
    if reservation.status != ReservationStatus.EN_ATTENTE:
        raise HttpError(400, "Cette réservation a déjà été traitée.")
    old_status = reservation.status
    reservation.status = payload.status
    reservation.validated_by = request.auth
    reservation.validated_at = timezone.now()
    if payload.notes:
        reservation.notes = payload.notes
    reservation.save()

    if payload.status == ReservationStatus.VALIDEE:
        grave = reservation.grave
        grave.status = GraveStatus.RESERVE
        grave.save(update_fields=["status", "updated_at"])

    log_action(request.auth, "update", "reservations", record_id=reservation.id, old_values={"status": old_status}, new_values={"status": reservation.status})
    if reservation.created_by_id and reservation.created_by_id != request.auth.id:
        verbe = "validée" if payload.status == ReservationStatus.VALIDEE else "refusée"
        notify_user(
            reservation.created_by, "reservation", f"Réservation {verbe}",
            f"La réservation pour {reservation.defunt_prenom} {reservation.defunt_nom} a été {verbe}.",
            reference_id=reservation.id,
        )
    return _out(reservation)


@router.post("/{reservation_id}/archive", response=ReservationOut)
def archive_reservation(request, reservation_id: str):
    require_manager(request)
    reservation = get_object_or_404(Reservation, id=reservation_id)
    if reservation.status not in (ReservationStatus.VALIDEE, ReservationStatus.REFUSEE):
        raise HttpError(400, "Seules les réservations validées ou refusées peuvent être archivées.")
    reservation.status = ReservationStatus.ARCHIVEE
    reservation.save(update_fields=["status", "updated_at"])
    log_action(request.auth, "update", "reservations", record_id=reservation.id, new_values={"status": "archivee"})
    return _out(reservation)


@router.get("/stats", response=ReservationStatsOut)
def reservation_stats(request):
    require_staff(request)
    now = timezone.now()
    agg = Reservation.objects.aggregate(
        total=Count("id"),
        en_attente=Count("id", filter=Q(status=ReservationStatus.EN_ATTENTE)),
        validee=Count("id", filter=Q(status=ReservationStatus.VALIDEE)),
        refusee=Count("id", filter=Q(status=ReservationStatus.REFUSEE)),
        ce_mois=Count("id", filter=Q(created_at__year=now.year, created_at__month=now.month)),
    )
    return ReservationStatsOut(**agg)


# Route dynamique déclarée en dernier pour ne pas intercepter les chemins
# statiques ci-dessus (Django résout les URLs dans l'ordre de déclaration).
@router.delete("/{reservation_id}")
def delete_reservation(request, reservation_id: str):
    require_admin(request)
    reservation = get_object_or_404(Reservation, id=reservation_id)
    log_action(request.auth, "delete", "reservations", record_id=reservation.id, old_values={"famille": reservation.famille_nom})
    reservation.delete()
    return {"detail": "Réservation supprimée."}
