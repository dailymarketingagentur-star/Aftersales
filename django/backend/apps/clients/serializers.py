from rest_framework import serializers

from apps.clients.models import Client, ClientKeyFact, Service, ServiceType


# ---------------------------------------------------------------------------
# ServiceType
# ---------------------------------------------------------------------------
class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = ["id", "name", "slug", "is_default", "position", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "is_default", "created_at", "updated_at"]


class ServiceTypeCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    position = serializers.IntegerField(required=False, default=0)


class ServiceTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = ["name", "position"]


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id", "name", "slug",
            "contact_first_name", "contact_last_name", "contact_email", "contact_phone", "website", "cloud_storage_url",
            "start_date", "monthly_volume", "tier",
            "status", "health_score", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "monthly_volume", "tier", "created_at", "updated_at"]


class ClientCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    contact_first_name = serializers.CharField(max_length=255, required=False, default="")
    contact_last_name = serializers.CharField(max_length=255, required=False, default="")
    contact_email = serializers.EmailField(required=False, default="")
    contact_phone = serializers.CharField(max_length=50, required=False, default="")
    website = serializers.URLField(required=False, default="")
    start_date = serializers.DateField(required=False, allow_null=True, default=None)
    status = serializers.ChoiceField(choices=Client.Status.choices, required=False, default="onboarding")
    notes = serializers.CharField(required=False, default="")


class ClientUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "name", "contact_first_name", "contact_last_name", "contact_email", "contact_phone", "website", "cloud_storage_url",
            "start_date", "status", "health_score", "notes",
        ]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class ServiceSerializer(serializers.ModelSerializer):
    service_type_name = serializers.CharField(source="service_type.name", read_only=True)

    class Meta:
        model = Service
        fields = [
            "id", "client", "service_type", "service_type_name",
            "name", "status", "start_date", "end_date",
            "monthly_budget", "link", "description",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "client", "created_at", "updated_at"]


class ServiceCreateSerializer(serializers.Serializer):
    service_type = serializers.UUIDField()
    name = serializers.CharField(max_length=255)
    status = serializers.ChoiceField(choices=Service.Status.choices, required=False, default="active")
    start_date = serializers.DateField(required=False, allow_null=True, default=None)
    end_date = serializers.DateField(required=False, allow_null=True, default=None)
    monthly_budget = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default="0.00")
    link = serializers.URLField(max_length=500, required=False, default="")
    description = serializers.CharField(required=False, default="")

    def validate_service_type(self, value):
        """Ensure service_type exists for the tenant."""
        tenant = self.context.get("tenant")
        if tenant and not ServiceType.objects.filter(id=value, tenant=tenant).exists():
            raise serializers.ValidationError("Service-Typ nicht gefunden.")
        return value


class ServiceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "service_type", "name", "status", "start_date", "end_date",
            "monthly_budget", "link", "description",
        ]


# ---------------------------------------------------------------------------
# ClientKeyFact
# ---------------------------------------------------------------------------
class ClientKeyFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientKeyFact
        fields = ["id", "label", "value", "position", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ClientKeyFactCreateSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=255)
    value = serializers.CharField()
    position = serializers.IntegerField(required=False, default=0)
