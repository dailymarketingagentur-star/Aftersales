from rest_framework import serializers

from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "is_active", "settings", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "is_active", "created_at", "updated_at"]


class TenantCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class TenantUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["name", "settings"]
