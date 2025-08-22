from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "corp", "category", "title", "file", "language", "content_type", "uploaded_by", "sha256", "created_at"]
        read_only_fields = ["uploaded_by", "sha256", "created_at", "content_type"]
