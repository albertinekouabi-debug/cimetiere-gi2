import uuid
from datetime import date, datetime
from typing import Optional, Any
from ninja import Schema


# ─── Section ──────────────────────────────────────────────────────────────────
class SectionIn(Schema):
    nom: str
    description: Optional[str] = None
    superficie: Optional[float] = None
    geojson: Optional[Any] = None


class SectionOut(Schema):
    id: uuid.UUID
    nom: str
    description: Optional[str] = None
    superficie: Optional[float] = None
    geojson: Optional[Any] = None
    created_at: datetime
    updated_at: datetime


# ─── Bloc ─────────────────────────────────────────────────────────────────────
class BlocIn(Schema):
    section_id: uuid.UUID
    nom: str
    description: Optional[str] = None
    geojson: Optional[Any] = None


class BlocOut(Schema):
    id: uuid.UUID
    section_id: uuid.UUID
    section_nom: Optional[str] = None
    nom: str
    description: Optional[str] = None
    geojson: Optional[Any] = None
    created_at: datetime
    updated_at: datetime


# ─── Grave (Caveau) ────────────────────────────────────────────────────────────
class GraveIn(Schema):
    bloc_id: uuid.UUID
    numero: str
    status: str = "libre"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geojson: Optional[Any] = None
    superficie: Optional[float] = None
    notes: Optional[str] = None


class GraveOut(Schema):
    id: uuid.UUID
    bloc_id: uuid.UUID
    bloc_nom: Optional[str] = None
    section_nom: Optional[str] = None
    numero: str
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geojson: Optional[Any] = None
    superficie: Optional[float] = None
    notes: Optional[str] = None
    nb_defunts: int = 0
    created_at: datetime
    updated_at: datetime


# ─── Défunt ───────────────────────────────────────────────────────────────────
class DefuntIn(Schema):
    nom: str
    prenom: str
    date_naissance: Optional[date] = None
    date_deces: date
    lieu_naissance: Optional[str] = None
    nationalite: Optional[str] = None
    grave_id: Optional[uuid.UUID] = None


class DefuntOut(Schema):
    id: uuid.UUID
    nom: str
    prenom: str
    date_naissance: Optional[date] = None
    date_deces: date
    lieu_naissance: Optional[str] = None
    nationalite: Optional[str] = None
    grave_id: Optional[uuid.UUID] = None
    grave_numero: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime


# ─── Statistiques ─────────────────────────────────────────────────────────────
class OccupancyStatsOut(Schema):
    total: int
    libre: int
    occupe: int
    reserve: int
    maintenance: int
    taux_occupation: float
