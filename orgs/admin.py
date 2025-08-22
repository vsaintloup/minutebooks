from django.contrib import admin
from .models import Organization, Membership

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = ["user"]  # marche car UserAdmin a des search_fields

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "created_at")
    search_fields = ("name",)
    inlines = [MembershipInline]

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("org", "user", "role", "is_active", "created_at", "id")
    list_filter = ("role", "is_active", "org")
    search_fields = ("org__name", "user__username", "user__email")
    autocomplete_fields = ["org", "user"]
