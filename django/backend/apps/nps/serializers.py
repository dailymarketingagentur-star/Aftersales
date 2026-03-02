from rest_framework import serializers

from apps.nps.models import NPSCampaign, NPSResponse, NPSSurvey, TestimonialRequest


# ---------------------------------------------------------------------------
# Public (no auth)
# ---------------------------------------------------------------------------
class PublicSurveySerializer(serializers.Serializer):
    """Read-only data for the public survey page."""

    tenant_name = serializers.CharField()
    client_first_name = serializers.CharField()
    is_expired = serializers.BooleanField()
    is_responded = serializers.BooleanField()


class SubmitResponseSerializer(serializers.Serializer):
    """Write serializer for submitting an NPS response."""

    score = serializers.IntegerField(min_value=0, max_value=10)
    comment = serializers.CharField(required=False, allow_blank=True, default="")


# ---------------------------------------------------------------------------
# NPSCampaign
# ---------------------------------------------------------------------------
class NPSCampaignSerializer(serializers.ModelSerializer):
    email_template_name = serializers.CharField(source="email_template.name", read_only=True, default=None)

    class Meta:
        model = NPSCampaign
        fields = [
            "id", "name", "slug", "trigger_type", "day_offset",
            "repeat_interval_days", "is_active", "email_template",
            "email_template_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class NPSCampaignCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    trigger_type = serializers.ChoiceField(choices=NPSCampaign.TriggerType.choices, default="day_offset")
    day_offset = serializers.IntegerField(default=90, min_value=0)
    repeat_interval_days = serializers.IntegerField(default=90, min_value=0)
    is_active = serializers.BooleanField(default=True)
    email_template = serializers.UUIDField(required=False, allow_null=True)


# ---------------------------------------------------------------------------
# NPSSurvey
# ---------------------------------------------------------------------------
class NPSSurveySerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    client_slug = serializers.CharField(source="client.slug", read_only=True)
    has_response = serializers.SerializerMethodField()

    class Meta:
        model = NPSSurvey
        fields = [
            "id", "campaign", "client", "client_name", "client_slug",
            "token", "status", "sent_at", "expires_at",
            "has_response", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_has_response(self, obj):
        return hasattr(obj, "response")


class SendSurveySerializer(serializers.Serializer):
    """Manually send a survey to a client."""

    client_id = serializers.UUIDField()
    campaign_id = serializers.UUIDField(required=False, allow_null=True)


# ---------------------------------------------------------------------------
# NPSResponse
# ---------------------------------------------------------------------------
class NPSResponseSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    client_slug = serializers.CharField(source="client.slug", read_only=True)

    class Meta:
        model = NPSResponse
        fields = [
            "id", "survey", "client", "client_name", "client_slug",
            "score", "segment", "comment", "responded_at",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# TestimonialRequest
# ---------------------------------------------------------------------------
class TestimonialRequestSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    client_slug = serializers.CharField(source="client.slug", read_only=True)

    class Meta:
        model = TestimonialRequest
        fields = [
            "id", "nps_response", "client", "client_name", "client_slug",
            "request_type", "status", "content", "platform_url",
            "requested_at", "received_at", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "nps_response", "client", "client_name", "client_slug", "requested_at", "created_at", "updated_at"]


class TestimonialCreateSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    nps_response_id = serializers.UUIDField(required=False, allow_null=True)
    request_type = serializers.ChoiceField(choices=TestimonialRequest.RequestType.choices, default="written")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class NPSDashboardSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    total = serializers.IntegerField()
    promoters = serializers.IntegerField()
    passives = serializers.IntegerField()
    detractors = serializers.IntegerField()
    promoter_pct = serializers.FloatField()
    passive_pct = serializers.FloatField()
    detractor_pct = serializers.FloatField()
    surveys_sent = serializers.IntegerField()
    surveys_responded = serializers.IntegerField()
    response_rate = serializers.FloatField()


class NPSTrendPointSerializer(serializers.Serializer):
    month = serializers.CharField()
    score = serializers.IntegerField()
    total = serializers.IntegerField()
