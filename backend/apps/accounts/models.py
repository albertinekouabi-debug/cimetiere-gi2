import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Administrateur"
    GESTIONNAIRE = "gestionnaire", "Gestionnaire"
    AGENT = "agent", "Agent"


class User(AbstractUser):
    """Utilisateur du système. Equivalent de la table `profiles` Supabase,
    fusionnée ici avec l'authentification Django (un seul modèle)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True, default="")
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.AGENT)
    phone = models.CharField(max_length=30, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name or self.email} ({self.role})"
