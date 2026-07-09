import uuid
from datetime import date, datetime
from typing import Optional
from ninja import Schema


class ReservationIn(Schema):
    grave_id: uuid.UUID
    defunt_nom: str
    defunt_prenom: str
    defunt_date_deces: date
    famille_nom: str
    famille_contact: Optional[str] = None
    famille_email: Optional[str] = None
    notes: Optional[str] = None


class ReservationOut(Schema):
    id: uuid.UUID
    grave_id: uuid.UUID
    grave_numero: Optional[str] = None
    defunt_nom: str
    defunt_prenom: str
    defunt_date_deces: date
    famille_nom: str
    famille_contact: Optional[str] = None
    famille_email: Optional[str] = None
    status: str
    created_by_nom: Optional[str] = None
    validated_by_nom: Optional[str] = None
    validated_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReservationValidateIn(Schema):
    status: str  # "validee" | "refusee"
    notes: Optional[str] = None


class ReservationStatsOut(Schema):
    total: int
    en_attente: int
    validee: int
    refusee: int
    ce_mois: int
