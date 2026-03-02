from django.contrib import admin

from apps.nps.models import NPSCampaign, NPSResponse, NPSSurvey, TestimonialRequest


@admin.register(NPSCampaign)
class NPSCampaignAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "trigger_type", "day_offset", "repeat_interval_days", "is_active"]
    list_filter = ["trigger_type", "is_active", "tenant"]
    search_fields = ["name", "slug"]
    raw_id_fields = ["tenant", "email_template"]


@admin.register(NPSSurvey)
class NPSSurveyAdmin(admin.ModelAdmin):
    list_display = ["token", "client", "tenant", "status", "sent_at", "expires_at"]
    list_filter = ["status", "tenant"]
    search_fields = ["client__name", "token"]
    raw_id_fields = ["tenant", "client", "campaign", "task", "email_log"]
    readonly_fields = ["token"]


@admin.register(NPSResponse)
class NPSResponseAdmin(admin.ModelAdmin):
    list_display = ["client", "score", "segment", "responded_at", "tenant"]
    list_filter = ["segment", "tenant"]
    search_fields = ["client__name", "comment"]
    raw_id_fields = ["tenant", "client", "survey"]
    readonly_fields = ["segment"]


@admin.register(TestimonialRequest)
class TestimonialRequestAdmin(admin.ModelAdmin):
    list_display = ["client", "request_type", "status", "requested_at", "received_at", "tenant"]
    list_filter = ["request_type", "status", "tenant"]
    search_fields = ["client__name", "content"]
    raw_id_fields = ["tenant", "client", "nps_response", "task"]
