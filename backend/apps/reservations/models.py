from django.conf import settings
from django.db import models
from apps.core.models import BaseModel
from apps.cemetery.models import Grave


class ReservationStatus(models.TextChoices):
    EN_ATTENTE = "en_attente", "En attente"
    VALIDEE = "validee", "Validée"
    REFUSEE = "refusee", "Refusée"
    ARCHIVEE = "archivee", "Archivée"


class Reservation(BaseModel):
    grave = models.ForeignKey(Grave, on_delete=models.CASCADE, related_name="reservations")
    defunt_nom = models.CharField(max_length=150)
    defunt_prenom = models.CharField(max_length=150)
    defunt_date_deces = models.DateField()
    famille_nom = models.CharField(max_length=200)
    famille_contact = models.CharField(max_length=50, blank=True, null=True)
    famille_email = models.EmailField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=ReservationStatus.choices, default=ReservationStatus.EN_ATTENTE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="reservations_created")
    validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations_validated")
    validated_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["status"])]
