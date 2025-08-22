# corps/serializers.py
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import ShareLink
from orgs.models import Membership

class ShareLinkSerializer(serializers.ModelSerializer):
    # on permet de passer une durée en jours (facultatif)
    expires_in_days = serializers.IntegerField(write_only=True, required=False, min_value=1, max_value=365)

    class Meta:
        model = ShareLink
        fields = ["id", "corp", "purpose", "note", "token", "expires_at", "is_active", "created_by", "created_at", "expires_in_days"]
        read_only_fields = ["id", "token", "created_by", "created_at"]

    def validate(self, attrs):
        request = self.context["request"]
        corp = attrs.get("corp") or getattr(self.instance, "corp", None)
        if not request.user.is_superuser and not Membership.objects.filter(org=corp.org, user=request.user, is_active=True).exists():
            raise serializers.ValidationError("Vous devez être membre actif de l'organisation de cette société.")
        return attrs

    def create(self, validated_data):
        days = validated_data.pop("expires_in_days", None)
        if days:
            validated_data["expires_at"] = timezone.now() + timedelta(days=days)
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
