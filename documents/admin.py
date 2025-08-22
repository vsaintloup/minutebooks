from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("corp", "title", "category", "language", "content_type", "uploaded_by", "created_at", "id")
    list_filter = ("corp", "category", "language", "content_type")
    search_fields = ("title", "corp__legal_name", "uploaded_by__username", "uploaded_by__email")
    readonly_fields = ("sha256", "created_at")
    autocomplete_fields = ["corp", "uploaded_by"]
