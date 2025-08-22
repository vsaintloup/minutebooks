from django.db import models
import secrets
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from orgs.models import Organization

class Address(models.Model):
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    province_state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, default="CA")

class Corporation(models.Model):
    class Jurisdiction(models.TextChoices):
        CBCA = "CBCA", "Fédéral (LCSA)"
        QC = "QC", "Québec (LSAQ)"

    org = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="corporations")
    legal_name = models.CharField(max_length=255)
    doing_business_as = models.CharField(max_length=255, blank=True)
    jurisdiction = models.CharField(max_length=10, choices=Jurisdiction.choices)
    incorporation_number = models.CharField(max_length=50, blank=True)
    business_number = models.CharField(max_length=15, blank=True)
    registered_office = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="registered_for")
    records_office = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="records_for")
    fiscal_year_end_month = models.PositiveSmallIntegerField(default=12)
    fiscal_year_end_day = models.PositiveSmallIntegerField(default=31)
    language_pref = models.CharField(max_length=5, default="fr")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        if self.doing_business_as:
            return f"{self.legal_name} (d/b/a {self.doing_business_as})"
        return self.legal_name or f"Corporation #{self.pk}"

class Person(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)  # requis pour ISC/BUO (si applicable)
    citizenship = models.CharField(max_length=100, blank=True)
    tax_residence = models.CharField(max_length=100, blank=True)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)

class Entity(models.Model):
    legal_name = models.CharField(max_length=255)
    jurisdiction = models.CharField(max_length=50, blank=True)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)

class Party(models.Model):
    class Type(models.TextChoices):
        PERSON = "PERSON", "Person"
        ENTITY = "ENTITY", "Entity"
    type = models.CharField(max_length=10, choices=Type.choices)
    person = models.ForeignKey(Person, null=True, blank=True, on_delete=models.CASCADE)
    entity = models.ForeignKey(Entity, null=True, blank=True, on_delete=models.CASCADE)

class Director(models.Model):
    corp = models.ForeignKey(Corporation, on_delete=models.CASCADE, related_name="directors")
    party = models.ForeignKey(Party, on_delete=models.PROTECT)
    residential_address = models.ForeignKey(Address, on_delete=models.PROTECT)
    started_on = models.DateField()
    ended_on = models.DateField(null=True, blank=True)

class Officer(models.Model):
    corp = models.ForeignKey(Corporation, on_delete=models.CASCADE, related_name="officers")
    party = models.ForeignKey(Party, on_delete=models.PROTECT)
    title = models.CharField(max_length=100)
    started_on = models.DateField()
    ended_on = models.DateField(null=True, blank=True)

class ShareLink(models.Model):
    PURPOSE_MINUTE_BOOK_RO = "minute_book_ro"
    PURPOSE_CHOICES = (
        (PURPOSE_MINUTE_BOOK_RO, "Lecture seule du livre de société"),
    )

    corp = models.ForeignKey("corps.Corporation", on_delete=models.CASCADE, related_name="share_links")
    token = models.SlugField(max_length=64, unique=True, db_index=True, editable=False)
    purpose = models.CharField(max_length=40, choices=PURPOSE_CHOICES, default=PURPOSE_MINUTE_BOOK_RO)
    note = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_sharelinks")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=14)
        super().save(*args, **kwargs)

    @property
    def is_valid(self) -> bool:
        return self.is_active and (self.expires_at is None or timezone.now() < self.expires_at)

    def __str__(self):
        return f"{self.corp} · {self.get_purpose_display()} · exp {self.expires_at:%Y-%m-%d}"
