from django.conf import settings
from django.db import models
from apps.core.models import BaseModel


class NotificationType(models.TextChoices):
    RESERVATION = "reservation", "Réservation"
    CONCESSION = "concession", "Concession"
    PAIEMENT = "paiement", "Paiement"
    SYSTEME = "systeme", "Système"


class Notification(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    titre = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    reference_id = models.CharField(max_length=64, null=True, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["user", "is_read"])]
