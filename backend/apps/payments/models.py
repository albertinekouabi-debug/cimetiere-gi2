import uuid
from django.conf import settings
from django.db import models
from apps.core.models import BaseModel
from apps.concessions.models import Concession


class PaymentMethod(models.TextChoices):
    ESPECES = "especes", "Espèces"
    VIREMENT = "virement", "Virement"
    CHEQUE = "cheque", "Chèque"
    CARTE = "carte", "Carte bancaire"
    MOMO = "momo", "MTN Mobile Money"


class Paiement(BaseModel):
    concession = models.ForeignKey(Concession, on_delete=models.CASCADE, related_name="paiements")
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date_paiement = models.DateField()
    mode_paiement = models.CharField(max_length=20, choices=PaymentMethod.choices)
    numero_recu = models.CharField(max_length=50, unique=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="paiements_created")

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["numero_recu"])]

    def __str__(self):
        return self.numero_recu


class MomoTransactionStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    SUCCESSFUL = "SUCCESSFUL", "Réussi"
    FAILED = "FAILED", "Échoué"


class MomoTransaction(BaseModel):
    """Suit une opération de paiement mobile MTN MoMo (Collections - RequestToPay)."""
    reference_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # X-Reference-Id envoyé à MTN
    momo_financial_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    concession = models.ForeignKey(Concession, on_delete=models.CASCADE, related_name="momo_transactions")
    paiement = models.OneToOneField(Paiement, on_delete=models.SET_NULL, null=True, blank=True, related_name="momo_transaction")
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=MomoTransactionStatus.choices, default=MomoTransactionStatus.PENDING)
    payer_message = models.CharField(max_length=200, blank=True, null=True)
    payee_note = models.CharField(max_length=200, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)  # motif d'échec renvoyé par MTN
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="momo_transactions_initiated")

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["status"]), models.Index(fields=["reference_id"])]
