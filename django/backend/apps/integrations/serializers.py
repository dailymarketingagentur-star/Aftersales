from rest_framework import serializers

from apps.integrations.models import (
    ActionExecution,
    ActionSequence,
    ActionTemplate,
    ClientIntegrationData,
    JiraConnection,
    SequenceStep,
    StepLog,
    TenantIntegration,
    TwilioConnection,
)
from apps.integrations.config_copy_service import COPYABLE_TYPES
from apps.integrations.registry import INTEGRATION_TYPES, get_field_keys, get_valid_keys


# ---------------------------------------------------------------------------
# JiraConnection
# ---------------------------------------------------------------------------
class JiraConnectionSerializer(serializers.ModelSerializer):
    """Read serializer — never exposes the encrypted token."""

    class Meta:
        model = JiraConnection
        fields = [
            "id",
            "label",
            "jira_url",
            "jira_email",
            "config",
            "is_active",
            "last_tested_at",
            "last_test_success",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_tested_at", "last_test_success", "created_at", "updated_at"]


class JiraConnectionWriteSerializer(serializers.Serializer):
    """Write serializer for creating/updating a Jira connection."""

    label = serializers.CharField(max_length=255, required=False, default="Jira Cloud")
    jira_url = serializers.URLField()
    jira_email = serializers.EmailField()
    jira_api_token = serializers.CharField(write_only=True)
    config = serializers.JSONField(required=False, default=dict)

    def validate_jira_url(self, value):
        return value.rstrip("/")


# ---------------------------------------------------------------------------
# TwilioConnection
# ---------------------------------------------------------------------------
class TwilioConnectionSerializer(serializers.ModelSerializer):
    """Read serializer — never exposes the encrypted auth token."""

    class Meta:
        model = TwilioConnection
        fields = [
            "id",
            "label",
            "account_sid",
            "twiml_app_sid",
            "phone_number",
            "is_active",
            "last_tested_at",
            "last_test_success",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_tested_at", "last_test_success", "created_at", "updated_at"]


class TwilioConnectionWriteSerializer(serializers.Serializer):
    """Write serializer for creating/updating a Twilio connection."""

    label = serializers.CharField(max_length=255, required=False, default="Twilio Telefonie")
    account_sid = serializers.CharField(max_length=100)
    auth_token = serializers.CharField(write_only=True)
    twiml_app_sid = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=20)

    def validate_account_sid(self, value):
        import re

        if not re.match(r"^AC[a-f0-9]{32}$", value):
            raise serializers.ValidationError("Account SID muss mit 'AC' beginnen und 34 Zeichen lang sein.")
        return value

    def validate_twiml_app_sid(self, value):
        import re

        if not re.match(r"^AP[a-f0-9]{32}$", value):
            raise serializers.ValidationError("TwiML App SID muss mit 'AP' beginnen und 34 Zeichen lang sein.")
        return value

    def validate_phone_number(self, value):
        import re

        if not re.match(r"^\+[1-9]\d{1,14}$", value):
            raise serializers.ValidationError("Telefonnummer muss im E.164-Format sein (z.B. +4930123456).")
        return value


# ---------------------------------------------------------------------------
# ActionTemplate
# ---------------------------------------------------------------------------
class ActionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionTemplate
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "target_type",
            "method",
            "endpoint",
            "webhook_url",
            "auth_type",
            "body_json",
            "headers_json",
            "variables",
            "output_mapping",
            "is_active",
            "is_system",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]


class ActionTemplateCreateSerializer(serializers.ModelSerializer):
    auth_credentials = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = ActionTemplate
        fields = [
            "slug",
            "name",
            "description",
            "target_type",
            "method",
            "endpoint",
            "webhook_url",
            "auth_type",
            "auth_credentials",
            "body_json",
            "headers_json",
            "variables",
            "output_mapping",
        ]

    def validate(self, attrs):
        target_type = attrs.get("target_type", "jira")
        # Bei PATCH ist target_type ggf. nicht im Payload — vom Instanz-Objekt lesen
        if self.instance and "target_type" not in attrs:
            target_type = self.instance.target_type

        if target_type == "webhook":
            webhook_url = attrs.get("webhook_url", getattr(self.instance, "webhook_url", "") if self.instance else "")
            if not webhook_url:
                raise serializers.ValidationError({"webhook_url": "Webhook-URL ist erforderlich fuer target_type=webhook."})
        return attrs

    def create(self, validated_data):
        creds = validated_data.pop("auth_credentials", None)
        instance = super().create(validated_data)
        if creds:
            instance.set_auth_credentials(creds)
            instance.save(update_fields=["auth_credentials_encrypted"])
        return instance

    def update(self, instance, validated_data):
        creds = validated_data.pop("auth_credentials", None)
        instance = super().update(instance, validated_data)
        if creds:
            instance.set_auth_credentials(creds)
            instance.save(update_fields=["auth_credentials_encrypted"])
        return instance


# ---------------------------------------------------------------------------
# SequenceStep (nested)
# ---------------------------------------------------------------------------
class SequenceStepSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    template_slug = serializers.CharField(source="template.slug", read_only=True)

    class Meta:
        model = SequenceStep
        fields = [
            "id",
            "template",
            "template_name",
            "template_slug",
            "position",
            "delay_seconds",
            "is_active",
        ]
        read_only_fields = ["id"]


class SequenceStepWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SequenceStep
        fields = ["template", "position", "delay_seconds", "is_active"]


# ---------------------------------------------------------------------------
# ActionSequence
# ---------------------------------------------------------------------------
class ActionSequenceSerializer(serializers.ModelSerializer):
    steps = SequenceStepSerializer(many=True, read_only=True)
    step_count = serializers.SerializerMethodField()

    class Meta:
        model = ActionSequence
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "is_active",
            "steps",
            "step_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_step_count(self, obj):
        return obj.steps.filter(is_active=True).count()


class ActionSequenceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionSequence
        fields = ["slug", "name", "description"]


# ---------------------------------------------------------------------------
# StepLog (read-only)
# ---------------------------------------------------------------------------
class StepLogSerializer(serializers.ModelSerializer):
    template_slug = serializers.CharField(source="template.slug", read_only=True, default="")

    class Meta:
        model = StepLog
        fields = [
            "id",
            "position",
            "template",
            "template_slug",
            "method",
            "url",
            "request_body",
            "request_headers",
            "status_code",
            "response_body",
            "response_headers",
            "status",
            "error_message",
            "extracted_outputs",
            "duration_ms",
            "created_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# ActionExecution
# ---------------------------------------------------------------------------
class ActionExecutionSerializer(serializers.ModelSerializer):
    step_logs = StepLogSerializer(many=True, read_only=True)
    sequence_slug = serializers.CharField(source="sequence.slug", read_only=True, default="")
    template_slug = serializers.CharField(source="template.slug", read_only=True, default="")
    triggered_by_email = serializers.CharField(source="triggered_by.email", read_only=True, default="")

    class Meta:
        model = ActionExecution
        fields = [
            "id",
            "sequence",
            "sequence_slug",
            "template",
            "template_slug",
            "status",
            "input_context",
            "accumulated_context",
            "current_step",
            "error_message",
            "triggered_by",
            "triggered_by_email",
            "entity_type",
            "entity_id",
            "celery_task_id",
            "idempotency_key",
            "step_logs",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ActionExecutionListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views (no step_logs)."""

    sequence_slug = serializers.CharField(source="sequence.slug", read_only=True, default="")
    template_slug = serializers.CharField(source="template.slug", read_only=True, default="")
    triggered_by_email = serializers.CharField(source="triggered_by.email", read_only=True, default="")

    class Meta:
        model = ActionExecution
        fields = [
            "id",
            "sequence_slug",
            "template_slug",
            "status",
            "current_step",
            "error_message",
            "triggered_by_email",
            "entity_type",
            "entity_id",
            "created_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Execute action (input)
# ---------------------------------------------------------------------------
class ExecuteActionSerializer(serializers.Serializer):
    template_slug = serializers.SlugField()
    context = serializers.JSONField(required=False, default=dict)
    entity_type = serializers.CharField(required=False, default="")
    entity_id = serializers.CharField(required=False, default="")
    idempotency_key = serializers.CharField(required=False, default="")


class ExecuteSequenceSerializer(serializers.Serializer):
    sequence_slug = serializers.SlugField()
    context = serializers.JSONField(required=False, default=dict)
    entity_type = serializers.CharField(required=False, default="")
    entity_id = serializers.CharField(required=False, default="")
    idempotency_key = serializers.CharField(required=False, default="")


# ---------------------------------------------------------------------------
# Integration Types (Registry-based)
# ---------------------------------------------------------------------------
class IntegrationFieldSerializer(serializers.Serializer):
    """Read-only representation of a single field definition."""

    key = serializers.CharField()
    label = serializers.CharField()
    field_type = serializers.CharField()


class IntegrationTypeSerializer(serializers.Serializer):
    """Read-only representation of an integration type + its enabled status."""

    key = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    icon = serializers.CharField()
    fields = IntegrationFieldSerializer(many=True)
    is_enabled = serializers.BooleanField()


class TenantIntegrationToggleSerializer(serializers.Serializer):
    """Input for toggling an integration on/off."""

    integration_type = serializers.CharField()
    is_enabled = serializers.BooleanField()

    def validate_integration_type(self, value):
        if value not in get_valid_keys():
            raise serializers.ValidationError(f"Unbekannter Integrationstyp: {value}")
        return value


# ---------------------------------------------------------------------------
# Client Integration Data
# ---------------------------------------------------------------------------
class ClientIntegrationDataSerializer(serializers.ModelSerializer):
    """Read serializer for client integration data."""

    fields_def = serializers.SerializerMethodField()

    class Meta:
        model = ClientIntegrationData
        fields = ["id", "integration_type", "data", "fields_def", "created_at", "updated_at"]
        read_only_fields = fields

    def get_fields_def(self, obj):
        typedef = INTEGRATION_TYPES.get(obj.integration_type)
        if not typedef:
            return []
        return [{"key": f.key, "label": f.label, "field_type": f.field_type} for f in typedef.fields]


class ClientIntegrationDataWriteSerializer(serializers.Serializer):
    """Input for creating/updating client integration data (multiple types at once)."""

    integration_type = serializers.CharField()
    data = serializers.JSONField()

    def validate_integration_type(self, value):
        if value not in get_valid_keys():
            raise serializers.ValidationError(f"Unbekannter Integrationstyp: {value}")
        return value

    def validate(self, attrs):
        integration_type = attrs.get("integration_type")
        data = attrs.get("data", {})
        if not isinstance(data, dict):
            raise serializers.ValidationError({"data": "Muss ein Objekt sein."})

        valid_keys = get_field_keys(integration_type)
        invalid_keys = set(data.keys()) - valid_keys
        if invalid_keys:
            raise serializers.ValidationError({"data": f"Ungültige Felder: {', '.join(sorted(invalid_keys))}"})

        return attrs


# ---------------------------------------------------------------------------
# Config Copy
# ---------------------------------------------------------------------------
class CopySourceTenantSerializer(serializers.Serializer):
    """Response: available source tenants for config copy."""

    tenant_id = serializers.CharField()
    tenant_name = serializers.CharField()
    available_types = serializers.ListField(child=serializers.CharField())


class CopyConfigRequestSerializer(serializers.Serializer):
    """Input for copying integration configs from another tenant."""

    source_tenant_id = serializers.UUIDField()
    types = serializers.ListField(
        child=serializers.ChoiceField(choices=[(t, t) for t in COPYABLE_TYPES]),
        min_length=1,
    )
    overwrite = serializers.BooleanField(default=False)


class CopyConfigResultSerializer(serializers.Serializer):
    """Response: result of a config copy operation."""

    copied = serializers.ListField(child=serializers.CharField())
    skipped = serializers.ListField(child=serializers.CharField())
    errors = serializers.ListField(child=serializers.CharField())


# ---------------------------------------------------------------------------
# Jira Project Creation
# ---------------------------------------------------------------------------
class CreateJiraProjectSerializer(serializers.Serializer):
    """Input for creating a Jira project for a client."""

    project_name = serializers.CharField(max_length=255)
    project_key = serializers.CharField(max_length=10)

    def validate_project_key(self, value):
        import re

        if not re.match(r"^[A-Z][A-Z0-9]{1,9}$", value):
            raise serializers.ValidationError(
                "Projekt-Key muss mit einem Großbuchstaben beginnen, nur Großbuchstaben und Ziffern enthalten und 2-10 Zeichen lang sein."
            )
        return value
