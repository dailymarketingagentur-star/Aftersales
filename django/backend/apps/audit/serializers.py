from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True, default=None)

    class Meta:
        model = AuditEvent
        fields = [
            "id", "action", "entity_type", "entity_id",
            "user", "user_email", "before", "after",
            "ip_address", "created_at",
        ]
        read_only_fields = fields
