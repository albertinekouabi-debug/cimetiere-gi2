from typing import List, Optional
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from ninja import Router, Query
from ninja.errors import HttpError

from apps.accounts.auth import jwt_auth
from apps.core.permissions import require_staff, require_admin
from apps.audit.utils import log_action
from .models import Section, Bloc, Grave, Defunt, GraveStatus
from .schemas import (
    SectionIn, SectionOut, BlocIn, BlocOut, GraveIn, GraveOut,
    DefuntIn, DefuntOut, OccupancyStatsOut,
)

router = Router(tags=["Cimetière"], auth=jwt_auth)


# ─── Sections ─────────────────────────────────────────────────────────────────
@router.get("/sections", response=List[SectionOut], auth=None)
def list_sections(request):
    return list(Section.objects.all())


@router.post("/sections", response=SectionOut)
def create_section(request, payload: SectionIn):
    require_staff(request)
    section = Section.objects.create(**payload.dict())
    log_action(request.auth, "create", "sections", record_id=section.id, new_values=payload.dict())
    return section


@router.put("/sections/{section_id}", response=SectionOut)
def update_section(request, section_id: str, payload: SectionIn):
    require_staff(request)
    section = get_object_or_404(Section, id=section_id)
    old = {"nom": section.nom, "description": section.description}
    for f, v in payload.dict().items():
        setattr(section, f, v)
    section.save()
    log_action(request.auth, "update", "sections", record_id=section.id, old_values=old, new_values=payload.dict())
    return section


@router.delete("/sections/{section_id}")
def delete_section(request, section_id: str):
    require_admin(request)
    section = get_object_or_404(Section, id=section_id)
    log_action(request.auth, "delete", "sections", record_id=section.id, old_values={"nom": section.nom})
    section.delete()
    return {"detail": "Section supprimée."}


# ─── Blocs ────────────────────────────────────────────────────────────────────
def _bloc_out(b: Bloc) -> BlocOut:
    return BlocOut(
        id=b.id, section_id=b.section_id, section_nom=b.section.nom if b.section_id else None,
        nom=b.nom, description=b.description, geojson=b.geojson,
        created_at=b.created_at, updated_at=b.updated_at,
    )


@router.get("/blocs", response=List[BlocOut], auth=None)
def list_blocs(request):
    return [_bloc_out(b) for b in Bloc.objects.select_related("section").all()]


@router.post("/blocs", response=BlocOut)
def create_bloc(request, payload: BlocIn):
    require_staff(request)
    section = get_object_or_404(Section, id=payload.section_id)
    bloc = Bloc.objects.create(section=section, nom=payload.nom, description=payload.description, geojson=payload.geojson)
    log_action(request.auth, "create", "blocs", record_id=bloc.id, new_values=payload.dict(exclude={"section_id"}) | {"section_id": str(payload.section_id)})
    return _bloc_out(bloc)


@router.put("/blocs/{bloc_id}", response=BlocOut)
def update_bloc(request, bloc_id: str, payload: BlocIn):
    require_staff(request)
    bloc = get_object_or_404(Bloc, id=bloc_id)
    old = {"nom": bloc.nom, "section_id": str(bloc.section_id)}
    bloc.section = get_object_or_404(Section, id=payload.section_id)
    bloc.nom = payload.nom
    bloc.description = payload.description
    bloc.geojson = payload.geojson
    bloc.save()
    log_action(request.auth, "update", "blocs", record_id=bloc.id, old_values=old)
    return _bloc_out(bloc)


@router.delete("/blocs/{bloc_id}")
def delete_bloc(request, bloc_id: str):
    require_admin(request)
    bloc = get_object_or_404(Bloc, id=bloc_id)
    log_action(request.auth, "delete", "blocs", record_id=bloc.id, old_values={"nom": bloc.nom})
    bloc.delete()
    return {"detail": "Bloc supprimé."}


# ─── Caveaux (Graves) ───────────────────────────────────────────────────────────
def _grave_out(g: Grave) -> GraveOut:
    return GraveOut(
        id=g.id, bloc_id=g.bloc_id, bloc_nom=g.bloc.nom if g.bloc_id else None,
        section_nom=g.bloc.section.nom if g.bloc_id else None,
        numero=g.numero, status=g.status, latitude=g.latitude, longitude=g.longitude,
        geojson=g.geojson, superficie=g.superficie, notes=g.notes,
        nb_defunts=g.defunts.count() if g.pk else 0,
        created_at=g.created_at, updated_at=g.updated_at,
    )


@router.get("/graves", response=List[GraveOut], auth=None)
def list_graves(request, status: Optional[str] = Query(None), section_id: Optional[str] = Query(None)):
    qs = Grave.objects.select_related("bloc", "bloc__section").prefetch_related("defunts")
    if status:
        qs = qs.filter(status=status)
    if section_id:
        qs = qs.filter(bloc__section_id=section_id)
    return [_grave_out(g) for g in qs]


@router.get("/graves/{grave_id}", response=GraveOut, auth=None)
def get_grave(request, grave_id: str):
    g = get_object_or_404(Grave.objects.select_related("bloc", "bloc__section"), id=grave_id)
    return _grave_out(g)


@router.post("/graves", response=GraveOut)
def create_grave(request, payload: GraveIn):
    require_staff(request)
    bloc = get_object_or_404(Bloc, id=payload.bloc_id)
    if payload.status not in GraveStatus.values:
        raise HttpError(400, "Statut de caveau invalide.")
    grave = Grave.objects.create(
        bloc=bloc, numero=payload.numero, status=payload.status,
        latitude=payload.latitude, longitude=payload.longitude,
        geojson=payload.geojson, superficie=payload.superficie, notes=payload.notes,
    )
    log_action(request.auth, "create", "graves", record_id=grave.id, new_values={"numero": grave.numero, "status": grave.status})
    return _grave_out(grave)


@router.put("/graves/{grave_id}", response=GraveOut)
def update_grave(request, grave_id: str, payload: GraveIn):
    require_staff(request)
    grave = get_object_or_404(Grave, id=grave_id)
    old = {"numero": grave.numero, "status": grave.status}
    grave.bloc = get_object_or_404(Bloc, id=payload.bloc_id)
    grave.numero = payload.numero
    grave.status = payload.status
    grave.latitude = payload.latitude
    grave.longitude = payload.longitude
    grave.geojson = payload.geojson
    grave.superficie = payload.superficie
    grave.notes = payload.notes
    grave.save()
    log_action(request.auth, "update", "graves", record_id=grave.id, old_values=old, new_values={"numero": grave.numero, "status": grave.status})
    return _grave_out(grave)


@router.delete("/graves/{grave_id}")
def delete_grave(request, grave_id: str):
    require_admin(request)
    grave = get_object_or_404(Grave, id=grave_id)
    log_action(request.auth, "delete", "graves", record_id=grave.id, old_values={"numero": grave.numero})
    grave.delete()
    return {"detail": "Caveau supprimé."}


@router.get("/stats/occupancy", response=OccupancyStatsOut, auth=None)
def occupancy_stats(request):
    agg = Grave.objects.aggregate(
        total=Count("id"),
        libre=Count("id", filter=Q(status="libre")),
        occupe=Count("id", filter=Q(status="occupe")),
        reserve=Count("id", filter=Q(status="reserve")),
        maintenance=Count("id", filter=Q(status="maintenance")),
    )
    total = agg["total"] or 0
    taux = round((agg["occupe"] / total) * 100, 1) if total else 0.0
    return OccupancyStatsOut(**agg, taux_occupation=taux)


# ─── Défunts + recherche publique ────────────────────────────────────────────
def _defunt_out(d: Defunt) -> DefuntOut:
    return DefuntOut(
        id=d.id, nom=d.nom, prenom=d.prenom, date_naissance=d.date_naissance,
        date_deces=d.date_deces, lieu_naissance=d.lieu_naissance, nationalite=d.nationalite,
        grave_id=d.grave_id, grave_numero=d.grave.numero if d.grave_id else None,
        latitude=d.grave.latitude if d.grave_id else None,
        longitude=d.grave.longitude if d.grave_id else None,
        created_at=d.created_at,
    )


@router.get("/defunts", response=List[DefuntOut], auth=None)
def list_defunts(request):
    return [_defunt_out(d) for d in Defunt.objects.select_related("grave").all()]


@router.get("/defunts/recherche", response=List[DefuntOut], auth=None)
def search_defunts(request, q: str = Query(..., min_length=2)):
    """Recherche publique par nom/prénom (équivalent de PublicSearchPage)."""
    qs = Defunt.objects.select_related("grave").filter(Q(nom__icontains=q) | Q(prenom__icontains=q))[:50]
    return [_defunt_out(d) for d in qs]


@router.post("/defunts", response=DefuntOut)
def create_defunt(request, payload: DefuntIn):
    require_staff(request)
    grave = get_object_or_404(Grave, id=payload.grave_id) if payload.grave_id else None
    defunt = Defunt.objects.create(
        nom=payload.nom, prenom=payload.prenom, date_naissance=payload.date_naissance,
        date_deces=payload.date_deces, lieu_naissance=payload.lieu_naissance,
        nationalite=payload.nationalite, grave=grave,
    )
    if grave and grave.status == GraveStatus.LIBRE:
        grave.status = GraveStatus.OCCUPE
        grave.save(update_fields=["status", "updated_at"])
    log_action(request.auth, "create", "defunts", record_id=defunt.id, new_values={"nom": defunt.nom, "prenom": defunt.prenom})
    return _defunt_out(defunt)


@router.put("/defunts/{defunt_id}", response=DefuntOut)
def update_defunt(request, defunt_id: str, payload: DefuntIn):
    require_staff(request)
    defunt = get_object_or_404(Defunt, id=defunt_id)
    old = {"nom": defunt.nom, "prenom": defunt.prenom}
    defunt.nom = payload.nom
    defunt.prenom = payload.prenom
    defunt.date_naissance = payload.date_naissance
    defunt.date_deces = payload.date_deces
    defunt.lieu_naissance = payload.lieu_naissance
    defunt.nationalite = payload.nationalite
    defunt.grave = get_object_or_404(Grave, id=payload.grave_id) if payload.grave_id else None
    defunt.save()
    log_action(request.auth, "update", "defunts", record_id=defunt.id, old_values=old)
    return _defunt_out(defunt)


@router.delete("/defunts/{defunt_id}")
def delete_defunt(request, defunt_id: str):
    require_admin(request)
    defunt = get_object_or_404(Defunt, id=defunt_id)
    log_action(request.auth, "delete", "defunts", record_id=defunt.id, old_values={"nom": defunt.nom})
    defunt.delete()
    return {"detail": "Défunt supprimé."}
