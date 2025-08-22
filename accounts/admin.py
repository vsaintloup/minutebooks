from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + ((None, {"fields": ("preferred_language",)}),)
    list_display = DjangoUserAdmin.list_display + ("preferred_language",)
    search_fields = DjangoUserAdmin.search_fields + ("email", "username",)
