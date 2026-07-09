from django.conf import settings
from django.db import models
from apps.core.models import BaseModel
from apps.cemetery.models import Grave
from apps.concessions.models import Concession


class ExhumationStatus(models.TextChoices):
    PLANIFIE = "planifie", "Planifié"
    EN_COURS = "en_cours", "En cours"
    TERMINE = "termine", "Terminé"


class Exhumation(BaseModel):
    grave = models.ForeignKey(Grave, on_delete=models.CASCADE, related_name="exhumations")
    concession = models.ForeignKey(Concession, on_delete=models.SET_NULL, null=True, blank=True, related_name="exhumations")
    status = models.CharField(max_length=20, choices=ExhumationStatus.choices, default=ExhumationStatus.PLANIFIE)
    date_planifiee = models.DateField(null=True, blank=True)
    date_realisation = models.DateField(null=True, blank=True)
    motif = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="exhumations_created")

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["status"])]
