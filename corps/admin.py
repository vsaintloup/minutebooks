from django.contrib import admin
from .models import Address, Corporation, Person, Entity, Party, Director, Officer

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("line1", "city", "province_state", "country", "postal_code", "id")
    search_fields = ("line1", "city", "postal_code")

@admin.register(Corporation)
class CorporationAdmin(admin.ModelAdmin):
    list_display = ("legal_name", "jurisdiction", "org", "incorporation_number", "created_at", "id")
    list_filter = ("jurisdiction", "org")
    search_fields = ("legal_name", "doing_business_as", "incorporation_number", "business_number")
    autocomplete_fields = ["org", "registered_office", "records_office"]

# ✅ Admin dédié pour Party avec search_fields
@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ("__str__", "id")
    # Minimal et sûr : on cherche par id ; on raffinera plus tard si tu veux (ex.: 'person__...','entity__...')
    search_fields = ("id",)

# Enregistrement simple pour les autres
for model in (Person, Entity, Director, Officer):
    admin.site.register(model, type(f"{model.__name__}Admin", (admin.ModelAdmin,), {
        "list_display": ("__str__", "id"),
    }))
