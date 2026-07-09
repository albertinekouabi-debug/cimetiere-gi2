import csv
import io
from decimal import Decimal
from typing import List, Optional
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from ninja import Router, Query
from ninja.errors import HttpError

from apps.accounts.auth import jwt_auth
from apps.core.permissions import require_staff, require_manager, require_admin
from apps.audit.utils import log_action
from apps.notifications.utils import notify_roles, notify_user
from apps.concessions.models import Concession
from .models import Paiement, PaymentMethod, MomoTransaction, MomoTransactionStatus
from .momo import momo_client, MomoError
from .pdf_utils import generate_recu_pdf, generate_paiements_export_pdf
from .schemas import (
    PaiementIn, PaiementOut, FinancialStatsOut,
    MomoInitiateIn, MomoTransactionOut, MomoCallbackIn,
)

router = Router(tags=["Paiements"], auth=jwt_auth)


def _generate_numero_recu(date_paiement) -> str:
    prefix = f"REC-{date_paiement.year}{date_paiement.month:02d}"
    count = Paiement.objects.filter(numero_recu__startswith=prefix).count()
    return f"{prefix}-{count + 1:04d}"


def _out(p: Paiement) -> PaiementOut:
    return PaiementOut(
        id=p.id, concession_id=p.concession_id, famille_nom=p.concession.famille_nom if p.concession_id else None,
        grave_numero=p.concession.grave.numero if p.concession_id and p.concession.grave_id else None,
        montant=float(p.montant), date_paiement=p.date_paiement, mode_paiement=p.mode_paiement,
        numero_recu=p.numero_recu, notes=p.notes,
        created_by_nom=p.created_by.full_name if p.created_by_id else None, created_at=p.created_at,
    )


# ─── Paiements manuels ────────────────────────────────────────────────────────
@router.get("/", response=List[PaiementOut])
def list_paiements(request):
    require_manager(request)
    return [_out(p) for p in Paiement.objects.select_related("concession", "concession__grave", "created_by").all()]


@router.post("/", response=PaiementOut)
def create_paiement(request, payload: PaiementIn):
    require_manager(request)
    if payload.mode_paiement not in (PaymentMethod.ESPECES, PaymentMethod.VIREMENT, PaymentMethod.CHEQUE, PaymentMethod.CARTE):
        raise HttpError(400, "Mode de paiement invalide pour un enregistrement manuel.")
    concession = get_object_or_404(Concession, id=payload.concession_id)
    numero_recu = _generate_numero_recu(payload.date_paiement)
    paiement = Paiement.objects.create(
        concession=concession, montant=payload.montant, date_paiement=payload.date_paiement,
        mode_paiement=payload.mode_paiement, numero_recu=numero_recu, notes=payload.notes,
        created_by=request.auth,
    )
    log_action(request.auth, "create", "paiements", record_id=paiement.id, new_values={"numero_recu": numero_recu, "montant": str(paiement.montant)})
    notify_roles(
        {"admin", "gestionnaire"}, "paiement", "Nouveau paiement enregistré",
        f"{paiement.montant:,.0f} FCFA — {concession.famille_nom} — reçu {numero_recu}.".replace(",", " "),
        reference_id=paiement.id, exclude_user=request.auth,
    )
    return _out(paiement)


@router.get("/stats", response=FinancialStatsOut)
def financial_stats(request):
    require_staff(request)
    now = timezone.now()
    total = Paiement.objects.aggregate(s=Sum("montant"))["s"] or 0
    mois = Paiement.objects.filter(date_paiement__year=now.year, date_paiement__month=now.month).aggregate(s=Sum("montant"))["s"] or 0
    annee = Paiement.objects.filter(date_paiement__year=now.year).aggregate(s=Sum("montant"))["s"] or 0
    return FinancialStatsOut(
        total_revenus=float(total), revenus_mois=float(mois), revenus_annee=float(annee),
        nombre_paiements=Paiement.objects.count(),
    )


# ─── Export / reçus PDF (chemins statiques déclarés AVANT les routes
#     dynamiques "/{paiement_id}" pour éviter tout conflit de résolution
#     d'URL, Django essayant les patterns dans leur ordre de déclaration) ────
@router.get("/export/pdf")
def export_paiements_pdf(request, date_debut: Optional[str] = Query(None), date_fin: Optional[str] = Query(None)):
    require_manager(request)
    qs = Paiement.objects.select_related("concession", "concession__grave").all()
    if date_debut:
        qs = qs.filter(date_paiement__gte=date_debut)
    if date_fin:
        qs = qs.filter(date_paiement__lte=date_fin)
    pdf_bytes = generate_paiements_export_pdf(qs)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="export_paiements.pdf"'
    return response


@router.get("/export/csv")
def export_paiements_csv(request, date_debut: Optional[str] = Query(None), date_fin: Optional[str] = Query(None)):
    require_manager(request)
    qs = Paiement.objects.select_related("concession", "concession__grave", "created_by").all()
    if date_debut:
        qs = qs.filter(date_paiement__gte=date_debut)
    if date_fin:
        qs = qs.filter(date_paiement__lte=date_fin)

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["N° reçu", "Date", "Famille", "Caveau", "Mode de paiement", "Montant (FCFA)", "Enregistré par", "Notes"])
    for p in qs:
        writer.writerow([
            p.numero_recu, p.date_paiement.strftime("%d/%m/%Y"),
            p.concession.famille_nom if p.concession_id else "",
            p.concession.grave.numero if p.concession_id and p.concession.grave_id else "",
            p.get_mode_paiement_display(), f"{p.montant:.0f}",
            p.created_by.full_name if p.created_by_id else "",
            p.notes or "",
        ])
    # BOM UTF-8 pour un ouverture correcte des accents dans Excel
    csv_bytes = "\ufeff" + buf.getvalue()
    response = HttpResponse(csv_bytes, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="export_paiements.csv"'
    return response


@router.get("/{paiement_id}/recu")
def download_recu(request, paiement_id: str):
    require_staff(request)
    paiement = get_object_or_404(Paiement.objects.select_related("concession", "concession__grave"), id=paiement_id)
    pdf_bytes = generate_recu_pdf(paiement)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{paiement.numero_recu}.pdf"'
    return response


@router.delete("/{paiement_id}")
def delete_paiement(request, paiement_id: str):
    require_admin(request)
    paiement = get_object_or_404(Paiement, id=paiement_id)
    log_action(request.auth, "delete", "paiements", record_id=paiement.id, old_values={"numero_recu": paiement.numero_recu})
    paiement.delete()
    return {"detail": "Paiement supprimé."}


# ─── MTN MoMo ─────────────────────────────────────────────────────────────────
def _momo_out(t: MomoTransaction) -> MomoTransactionOut:
    return MomoTransactionOut(
        id=t.id, reference_id=t.reference_id, concession_id=t.concession_id, montant=float(t.montant),
        phone_number=t.phone_number, status=t.status, reason=t.reason, paiement_id=t.paiement_id,
        created_at=t.created_at, updated_at=t.updated_at,
    )


@router.post("/momo/initiate", response=MomoTransactionOut)
def momo_initiate(request, payload: MomoInitiateIn):
    """Déclenche un paiement MTN MoMo (Request To Pay) : le client reçoit une
    demande de paiement sur son téléphone et doit la valider avec son code PIN."""
    require_staff(request)
    concession = get_object_or_404(Concession, id=payload.concession_id)

    transaction = MomoTransaction.objects.create(
        concession=concession, montant=payload.montant, phone_number=payload.phone_number,
        payer_message=f"Concession {concession.grave.numero if concession.grave_id else ''}",
        payee_note=payload.notes or "Paiement concession funéraire",
        initiated_by=request.auth,
    )
    try:
        momo_client.request_to_pay(
            reference_id=transaction.reference_id, amount=Decimal(str(payload.montant)),
            phone_number=payload.phone_number, payer_message=transaction.payer_message,
            payee_note=transaction.payee_note,
        )
    except MomoError as e:
        transaction.status = MomoTransactionStatus.FAILED
        transaction.reason = str(e)
        transaction.save(update_fields=["status", "reason", "updated_at"])
        raise HttpError(502, str(e))

    log_action(request.auth, "create", "momo_transactions", record_id=transaction.id, new_values={"montant": str(transaction.montant), "phone": transaction.phone_number})
    return _momo_out(transaction)


@router.get("/momo/{reference_id}/status", response=MomoTransactionOut)
def momo_status(request, reference_id: str):
    """Interroge MTN MoMo pour connaître l'état d'une transaction, et si elle
    est réussie, crée automatiquement le paiement + reçu correspondant."""
    require_staff(request)
    transaction = get_object_or_404(MomoTransaction, reference_id=reference_id)

    if transaction.status == MomoTransactionStatus.PENDING:
        try:
            data = momo_client.get_transaction_status(transaction.reference_id)
        except MomoError as e:
            raise HttpError(502, str(e))

        mtn_status = data.get("status", "PENDING")
        if mtn_status == "SUCCESSFUL":
            _finalize_momo_success(transaction, data)
        elif mtn_status == "FAILED":
            transaction.status = MomoTransactionStatus.FAILED
            reason = data.get("reason", {})
            transaction.reason = reason.get("message") if isinstance(reason, dict) else str(reason)
            transaction.save(update_fields=["status", "reason", "updated_at"])

    return _momo_out(transaction)


def _finalize_momo_success(transaction: MomoTransaction, mtn_data: dict):
    transaction.status = MomoTransactionStatus.SUCCESSFUL
    transaction.momo_financial_transaction_id = mtn_data.get("financialTransactionId")
    if not transaction.paiement_id:
        numero_recu = _generate_numero_recu(timezone.now().date())
        paiement = Paiement.objects.create(
            concession=transaction.concession, montant=transaction.montant, date_paiement=timezone.now().date(),
            mode_paiement=PaymentMethod.MOMO, numero_recu=numero_recu,
            notes=f"Paiement MTN MoMo — réf. {transaction.reference_id}",
            created_by=transaction.initiated_by,
        )
        transaction.paiement = paiement
        log_action(transaction.initiated_by, "create", "paiements", record_id=paiement.id, new_values={"mode": "momo", "numero_recu": numero_recu})
        notify_user(
            transaction.initiated_by, "paiement", "Paiement MTN MoMo confirmé",
            f"Le paiement de {transaction.montant:,.0f} FCFA via MTN MoMo a été confirmé (reçu {numero_recu}).".replace(",", " "),
            reference_id=paiement.id,
        )
        notify_roles(
            {"admin", "gestionnaire"}, "paiement", "Paiement MTN MoMo confirmé",
            f"{transaction.montant:,.0f} FCFA — {transaction.concession.famille_nom} — reçu {numero_recu}.".replace(",", " "),
            reference_id=paiement.id, exclude_user=transaction.initiated_by,
        )
    transaction.save()


@router.post("/momo/callback", auth=None)
def momo_callback(request, payload: MomoCallbackIn):
    """Webhook appelé par MTN MoMo (X-Callback-Url) lorsqu'une transaction change
    d'état. Non authentifié par JWT (c'est MTN qui appelle), à sécuriser en
    production via une vérification d'IP/signature si fournie par MTN."""
    if not payload.referenceId:
        raise HttpError(400, "referenceId manquant.")
    try:
        transaction = MomoTransaction.objects.get(reference_id=payload.referenceId)
    except MomoTransaction.DoesNotExist:
        return {"detail": "Transaction inconnue, ignorée."}

    if payload.status == "SUCCESSFUL" and transaction.status != MomoTransactionStatus.SUCCESSFUL:
        _finalize_momo_success(transaction, {"financialTransactionId": payload.financialTransactionId})
    elif payload.status == "FAILED":
        transaction.status = MomoTransactionStatus.FAILED
        transaction.reason = (payload.reason or {}).get("message") if payload.reason else "Échec signalé par MTN MoMo."
        transaction.save(update_fields=["status", "reason", "updated_at"])
    return {"detail": "Callback traité."}


@router.get("/momo/transactions", response=List[MomoTransactionOut])
def list_momo_transactions(request):
    require_manager(request)
    return [_momo_out(t) for t in MomoTransaction.objects.all()]
