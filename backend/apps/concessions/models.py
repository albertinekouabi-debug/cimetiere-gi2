from django.db import models
from apps.core.models import BaseModel
from apps.cemetery.models import Grave
from apps.reservations.models import Reservation


class ConcessionDuration(models.TextChoices):
    DIX_ANS = "10_ans", "10 ans"
    TRENTE_ANS = "30_ans", "30 ans"
    PERPETUELLE = "perpetuelle", "Perpétuelle"


class ConcessionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIREE = "expiree", "Expirée"
    RESILIEE = "resiliee", "Résiliée"


DUREE_ANNEES = {
    ConcessionDuration.DIX_ANS: 10,
    ConcessionDuration.TRENTE_ANS: 30,
}


class Concession(BaseModel):
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True, related_name="concessions")
    grave = models.ForeignKey(Grave, on_delete=models.CASCADE, related_name="concessions")
    famille_nom = models.CharField(max_length=200)
    famille_contact = models.CharField(max_length=50, blank=True, null=True)
    famille_email = models.EmailField(blank=True, null=True)
    duree = models.CharField(max_length=20, choices=ConcessionDuration.choices)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=ConcessionStatus.choices, default=ConcessionStatus.ACTIVE)
    notes = models.TextField(blank=True, null=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["status"])]
