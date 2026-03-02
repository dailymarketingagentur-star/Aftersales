from rest_framework import serializers

from .models import TenantSubscription


class TenantSubscriptionSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = TenantSubscription
        fields = ["id", "status", "plan_name", "current_period_end", "is_active", "created_at", "updated_at"]
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    price_id = serializers.CharField()
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()


class PortalSerializer(serializers.Serializer):
    return_url = serializers.URLField()
