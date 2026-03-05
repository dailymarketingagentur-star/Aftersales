from rest_framework import serializers

from apps.emails.models import (
    EmailLog,
    EmailProviderConnection,
    EmailSequence,
    EmailTemplate,
    InboundEmail,
    SequenceEnrollment,
    SequenceStep,
    WhatsAppMessage,
)


# ------------------------------------------------------------------
# Email Provider Connection
# ------------------------------------------------------------------


class EmailProviderConnectionSerializer(serializers.ModelSerializer):
    """Read serializer — never exposes encrypted secrets."""

    class Meta:
        model = EmailProviderConnection
        fields = [
            "id", "provider_type", "label", "is_active",
            "smtp_host", "smtp_port", "smtp_username", "smtp_use_tls",
            "from_email", "from_name",
            "inbound_parse_enabled", "inbound_parse_domain",
            "last_tested_at", "last_test_success", "last_test_message",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class SmtpConnectionWriteSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=255, default="SMTP")
    smtp_host = serializers.CharField(max_length=255)
    smtp_port = serializers.IntegerField(default=587)
    smtp_username = serializers.CharField(max_length=255, required=False, allow_blank=True)
    smtp_password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    smtp_use_tls = serializers.BooleanField(default=True)
    from_email = serializers.EmailField()
    from_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class SendGridConnectionWriteSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=255, default="SendGrid")
    sendgrid_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    from_email = serializers.EmailField()
    from_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    inbound_parse_enabled = serializers.BooleanField(required=False, default=False)
    inbound_parse_domain = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


# ------------------------------------------------------------------
# Templates
# ------------------------------------------------------------------


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = [
            "id", "tenant", "slug", "name", "subject",
            "body_html", "body_text", "variables", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tenant", "created_at", "updated_at"]


class EmailTemplateCreateSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=100)
    name = serializers.CharField(max_length=255)
    subject = serializers.CharField(max_length=500)
    body_html = serializers.CharField()
    body_text = serializers.CharField(required=False, default="")
    variables = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class EmailTemplateUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    subject = serializers.CharField(max_length=500, required=False)
    body_html = serializers.CharField(required=False)
    body_text = serializers.CharField(required=False)
    variables = serializers.ListField(child=serializers.CharField(), required=False)
    is_active = serializers.BooleanField(required=False)


# ------------------------------------------------------------------
# Logs
# ------------------------------------------------------------------


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = [
            "id", "tenant", "template", "template_slug",
            "recipient_email", "subject", "status",
            "error_message", "context", "scheduled_at", "sent_at",
            "idempotency_key", "sequence_enrollment",
            "tracking_id", "opened_at", "clicked_at",
            "created_at",
        ]


# ------------------------------------------------------------------
# Send (action serializer)
# ------------------------------------------------------------------


class SendEmailSerializer(serializers.Serializer):
    template_slug = serializers.SlugField(max_length=100)
    recipient_email = serializers.EmailField()
    context = serializers.DictField(required=False, default=dict)
    idempotency_key = serializers.CharField(max_length=255, required=False, allow_blank=True)
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)


# ------------------------------------------------------------------
# Sequences
# ------------------------------------------------------------------


class SequenceStepSerializer(serializers.ModelSerializer):
    template_slug = serializers.CharField(source="template.slug", read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)

    class Meta:
        model = SequenceStep
        fields = [
            "id", "template", "template_slug", "template_name",
            "position", "delay_days", "delay_hours",
            "total_delay_seconds", "is_active",
        ]


class EmailSequenceSerializer(serializers.ModelSerializer):
    steps = SequenceStepSerializer(many=True, read_only=True)

    class Meta:
        model = EmailSequence
        fields = [
            "id", "tenant", "slug", "name", "description",
            "is_active", "steps", "created_at", "updated_at",
        ]


class StartSequenceSerializer(serializers.Serializer):
    sequence_slug = serializers.SlugField(max_length=100)
    recipient_email = serializers.EmailField()
    context = serializers.DictField(required=False, default=dict)


# ------------------------------------------------------------------
# Enrollments
# ------------------------------------------------------------------


class SequenceEnrollmentSerializer(serializers.ModelSerializer):
    sequence_slug = serializers.CharField(source="sequence.slug", read_only=True)
    sequence_name = serializers.CharField(source="sequence.name", read_only=True)

    class Meta:
        model = SequenceEnrollment
        fields = [
            "id", "tenant", "sequence", "sequence_slug", "sequence_name",
            "recipient_email", "context", "status",
            "started_at", "completed_at", "current_step",
            "created_at",
        ]


# ------------------------------------------------------------------
# Inbound Email
# ------------------------------------------------------------------


class InboundEmailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True, default=None)

    class Meta:
        model = InboundEmail
        fields = [
            "id", "from_email", "from_name", "to_email", "subject",
            "body_text", "client", "client_name", "has_attachments",
            "is_read", "is_assigned", "created_at",
        ]


# ------------------------------------------------------------------
# WhatsApp Messages
# ------------------------------------------------------------------


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True, default=None)

    class Meta:
        model = WhatsAppMessage
        fields = [
            "id", "wa_message_id", "direction", "from_number", "to_number",
            "body_text", "message_type", "status",
            "client", "client_name", "is_read", "metadata",
            "created_at",
        ]
