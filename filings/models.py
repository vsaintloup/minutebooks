from django.db import models
from corps.models import Corporation

class Filing(models.Model):
    class Type(models.TextChoices):
        CC_ANNUAL_RETURN = "CC_AR", "Corporations Canada — rapport annuel"
        REQ_ANNUAL = "REQ_ANNUAL", "REQ — mise à jour annuelle"
        REQ_EVENT = "REQ_EVENT", "REQ — mise à jour événementielle"
        ISC_UPDATE = "ISC_UPD", "Mise à jour ISC/BUO"
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        READY = "READY", "Prêt à déposer"
        FILED = "FILED", "Déposé"
        REJECTED = "REJECTED", "Rejeté"

    corp = models.ForeignKey(Corporation, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=Type.choices)
    due_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    reference = models.CharField(max_length=100, blank=True)  # numéro de confirmation, etc.
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
