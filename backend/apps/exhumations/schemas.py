import uuid
from datetime import date, datetime
from typing import Optional
from ninja import Schema


class ExhumationIn(Schema):
    grave_id: uuid.UUID
    concession_id: Optional[uuid.UUID] = None
    date_planifiee: Optional[date] = None
    motif: Optional[str] = None
    notes: Optional[str] = None


class ExhumationOut(Schema):
    id: uuid.UUID
    grave_id: uuid.UUID
    grave_numero: Optional[str] = None
    concession_id: Optional[uuid.UUID] = None
    status: str
    date_planifiee: Optional[date] = None
    date_realisation: Optional[date] = None
    motif: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ExhumationStatusIn(Schema):
    status: str
    date_realisation: Optional[date] = None
