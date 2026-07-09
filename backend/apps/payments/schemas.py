import uuid
from datetime import date, datetime
from typing import Optional
from ninja import Schema


class PaiementIn(Schema):
    concession_id: uuid.UUID
    montant: float
    date_paiement: date
    mode_paiement: str  # especes | virement | cheque | carte
    notes: Optional[str] = None


class PaiementOut(Schema):
    id: uuid.UUID
    concession_id: uuid.UUID
    famille_nom: Optional[str] = None
    grave_numero: Optional[str] = None
    montant: float
    date_paiement: date
    mode_paiement: str
    numero_recu: str
    notes: Optional[str] = None
    created_by_nom: Optional[str] = None
    created_at: datetime


class FinancialStatsOut(Schema):
    total_revenus: float
    revenus_mois: float
    revenus_annee: float
    nombre_paiements: int


# ─── MTN MoMo ─────────────────────────────────────────────────────────────────
class MomoInitiateIn(Schema):
    concession_id: uuid.UUID
    montant: float
    phone_number: str
    notes: Optional[str] = None


class MomoTransactionOut(Schema):
    id: uuid.UUID
    reference_id: uuid.UUID
    concession_id: uuid.UUID
    montant: float
    phone_number: str
    status: str
    reason: Optional[str] = None
    paiement_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class MomoCallbackIn(Schema):
    """Corps du callback envoyé par MTN MoMo (schéma simplifié, best-effort)."""
    referenceId: Optional[str] = None
    status: Optional[str] = None
    financialTransactionId: Optional[str] = None
    reason: Optional[dict] = None
