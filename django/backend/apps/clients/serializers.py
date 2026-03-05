from rest_framework import serializers

from apps.clients.models import (
    ChurnWarningAssessment,
    Client,
    ClientEmailAddress,
    ClientKeyFact,
    ClientPhoneNumber,
    HealthScoreAssessment,
    Service,
    ServiceType,
)


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
# ClientPhoneNumber / ClientEmailAddress
# ---------------------------------------------------------------------------
class ClientPhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientPhoneNumber
        fields = ["id", "label", "number", "position", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ClientPhoneNumberCreateSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=255, required=False, default="")
    number = serializers.CharField(max_length=50)
    position = serializers.IntegerField(required=False, default=0)


class ClientEmailAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientEmailAddress
        fields = ["id", "label", "email", "position", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ClientEmailAddressCreateSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=255, required=False, default="")
    email = serializers.EmailField()
    position = serializers.IntegerField(required=False, default=0)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
class ClientSerializer(serializers.ModelSerializer):
    phone_numbers = ClientPhoneNumberSerializer(many=True, read_only=True)
    email_addresses = ClientEmailAddressSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = [
            "id", "name", "slug",
            "contact_first_name", "contact_last_name", "contact_email", "contact_phone", "website", "cloud_storage_url",
            "start_date", "monthly_volume", "tier",
            "status", "health_score", "churn_warning_count",
            "last_health_assessment_at", "last_churn_assessment_at",
            "notes",
            "phone_numbers", "email_addresses",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "slug", "monthly_volume", "tier", "health_score",
            "churn_warning_count", "last_health_assessment_at", "last_churn_assessment_at",
            "created_at", "updated_at",
        ]


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
            "start_date", "status", "notes",
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


# ---------------------------------------------------------------------------
# Health Score Assessment
# ---------------------------------------------------------------------------
class HealthScoreAssessmentSerializer(serializers.ModelSerializer):
    assessed_by_email = serializers.EmailField(source="assessed_by.email", read_only=True, default=None)
    status_label = serializers.CharField(read_only=True)

    class Meta:
        model = HealthScoreAssessment
        fields = [
            "id",
            "result_satisfaction", "communication", "engagement", "relationship",
            "payment_behavior", "growth_potential", "referral_readiness",
            "total_score", "status_label", "notes",
            "assessed_by", "assessed_by_email",
            "created_at",
        ]
        read_only_fields = ["id", "total_score", "assessed_by", "created_at"]


class HealthScoreSubmitSerializer(serializers.Serializer):
    result_satisfaction = serializers.IntegerField(min_value=1, max_value=5)
    communication = serializers.IntegerField(min_value=1, max_value=5)
    engagement = serializers.IntegerField(min_value=1, max_value=5)
    relationship = serializers.IntegerField(min_value=1, max_value=5)
    payment_behavior = serializers.IntegerField(min_value=1, max_value=5)
    growth_potential = serializers.IntegerField(min_value=1, max_value=5)
    referral_readiness = serializers.IntegerField(min_value=1, max_value=5)
    notes = serializers.CharField(required=False, default="")


# ---------------------------------------------------------------------------
# Churn Warning Assessment
# ---------------------------------------------------------------------------
class ChurnWarningAssessmentSerializer(serializers.ModelSerializer):
    assessed_by_email = serializers.EmailField(source="assessed_by.email", read_only=True, default=None)

    class Meta:
        model = ChurnWarningAssessment
        fields = [
            "id",
            "slower_responses", "missed_checkins", "decreased_usage", "contract_inquiries",
            "new_decision_maker", "budget_cuts_mentioned", "competitor_mentions",
            "critical_feedback", "delayed_payments", "fewer_approvals",
            "active_signals", "notes",
            "assessed_by", "assessed_by_email",
            "created_at",
        ]
        read_only_fields = ["id", "active_signals", "assessed_by", "created_at"]


class ChurnWarningSubmitSerializer(serializers.Serializer):
    slower_responses = serializers.BooleanField(default=False)
    missed_checkins = serializers.BooleanField(default=False)
    decreased_usage = serializers.BooleanField(default=False)
    contract_inquiries = serializers.BooleanField(default=False)
    new_decision_maker = serializers.BooleanField(default=False)
    budget_cuts_mentioned = serializers.BooleanField(default=False)
    competitor_mentions = serializers.BooleanField(default=False)
    critical_feedback = serializers.BooleanField(default=False)
    delayed_payments = serializers.BooleanField(default=False)
    fewer_approvals = serializers.BooleanField(default=False)
    notes = serializers.CharField(required=False, default="")
