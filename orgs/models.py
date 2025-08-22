from django.db import models
from django.conf import settings

class Organization(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_orgs")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name or f"Organization #{self.pk}"

class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        LAWYER = "LAWYER", "Lawyer"
        STAFF = "STAFF", "Staff"
        CLIENT_ADMIN = "CLIENT_ADMIN", "Client admin"
        VIEWER = "VIEWER", "Viewer"
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("org", "user")
