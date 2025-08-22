import os
from django.db import models
from django.conf import settings
from corps.models import Corporation

class Ticket(models.Model):
    class Category(models.TextChoices):
        RESOLUTION = "RESOLUTION", "Rédaction de résolution"
        FILING = "FILING", "Dépôt REQ/Corporations Canada"
        MIGRATION = "MIGRATION", "Migration livre papier"
        OTHER = "OTHER", "Autre"
    class Status(models.TextChoices):
        OPEN = "OPEN", "Ouvert"
        IN_PROGRESS = "IN_PROGRESS", "En cours"
        WAITING = "WAITING", "En attente du client"
        DONE = "DONE", "Terminé"

    corp = models.ForeignKey(Corporation, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=Category.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets_opened")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="tickets_assigned")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

def ticket_attachment_upload_to(instance, filename):
    base, ext = os.path.splitext(filename)
    # range les fichiers par ticket
    return f"tickets/{instance.ticket_id or 'tmp'}/{timezone.now():%Y%m%d%H%M%S}{ext}"

class TicketAttachment(models.Model):
    ticket = models.ForeignKey(
        "tickets.Ticket",
        related_name="attachments",
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to=ticket_attachment_upload_to)
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        name = self.original_name or os.path.basename(self.file.name)
        return f"{self.ticket_id} · {name}"

    def soft_delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=["is_deleted", "deleted_at"])

    def save(self, *args, **kwargs):
        if self.file and not self.original_name:
            self.original_name = os.path.basename(self.file.name)
        try:
            if self.file and hasattr(self.file, "size"):
                self.size = self.file.size
        except Exception:
            pass
        super().save(*args, **kwargs)
