from django.db import models
from apps.core.models import BaseModel


class Section(BaseModel):
    nom = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    geojson = models.JSONField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Bloc(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="blocs")
    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    geojson = models.JSONField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        ordering = ["nom"]
        unique_together = [("section", "nom")]

    def __str__(self):
        return f"{self.nom} ({self.section.nom})"


class GraveStatus(models.TextChoices):
    LIBRE = "libre", "Libre"
    OCCUPE = "occupe", "Occupé"
    RESERVE = "reserve", "Réservé"
    MAINTENANCE = "maintenance", "Maintenance"


class Grave(BaseModel):
    bloc = models.ForeignKey(Bloc, on_delete=models.CASCADE, related_name="graves")
    numero = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=GraveStatus.choices, default=GraveStatus.LIBRE)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geojson = models.JSONField(null=True, blank=True)
    superficie = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta(BaseModel.Meta):
        ordering = ["numero"]
        unique_together = [("bloc", "numero")]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return self.numero


class Defunt(BaseModel):
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    date_naissance = models.DateField(null=True, blank=True)
    date_deces = models.DateField()
    lieu_naissance = models.CharField(max_length=200, blank=True, null=True)
    nationalite = models.CharField(max_length=100, blank=True, null=True)
    grave = models.ForeignKey(Grave, on_delete=models.SET_NULL, null=True, blank=True, related_name="defunts")

    class Meta(BaseModel.Meta):
        ordering = ["nom", "prenom"]
        indexes = [models.Index(fields=["nom", "prenom"])]

    def __str__(self):
        return f"{self.nom} {self.prenom}"
