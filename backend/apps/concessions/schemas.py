import uuid
from datetime import date, datetime
from typing import Optional
from ninja import Schema


class ConcessionIn(Schema):
    grave_id: uuid.UUID
    reservation_id: Optional[uuid.UUID] = None
    famille_nom: str
    famille_contact: Optional[str] = None
    famille_email: Optional[str] = None
    duree: str
    date_debut: date
    montant_total: float
    notes: Optional[str] = None


class ConcessionOut(Schema):
    id: uuid.UUID
    grave_id: uuid.UUID
    grave_numero: Optional[str] = None
    reservation_id: Optional[uuid.UUID] = None
    famille_nom: str
    famille_contact: Optional[str] = None
    famille_email: Optional[str] = None
    duree: str
    date_debut: date
    date_fin: Optional[date] = None
    montant_total: float
    montant_paye: float = 0
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ConcessionRenewIn(Schema):
    nouvelle_duree: str
    montant_supplementaire: float = 0
