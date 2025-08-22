from rest_framework import serializers
from .models import Ticket, TicketAttachment

class TicketSerializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source="org.name", read_only=True)
    corp_name = serializers.CharField(source="corp.legal_name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id", "title", "description", "type", "status", "priority",
            "org", "org_name", "corp", "corp_name",
            "payload", "created_by", "created_by_username",
            "assigned_to", "assigned_to_username",
            "created_at", "updated_at", "closed_at",
        ]
        read_only_fields = ("status", "created_by", "created_at", "updated_at", "closed_at")

class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["title", "description", "type", "priority", "org", "corp", "payload"]

    def validate(self, data):
        # Cohérence org <-> corp
        if data["corp"].org_id != data["org"].id:
            raise serializers.ValidationError("La corporation ne correspond pas à l’organisation.")
        return data

class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = ["id", "ticket", "original_name", "file", "content_type", "size", "uploaded_by", "created_at"]
        read_only_fields = ["ticket", "content_type", "size", "uploaded_by", "created_at"]
