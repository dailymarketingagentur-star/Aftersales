from django.contrib import admin

from apps.emails.models import (
    EmailLog,
    EmailProviderConnection,
    EmailSequence,
    EmailTemplate,
    SequenceEnrollment,
    SequenceStep,
)


@admin.register(EmailProviderConnection)
class EmailProviderConnectionAdmin(admin.ModelAdmin):
    list_display = ["label", "provider_type", "tenant", "is_active", "from_email", "last_test_success", "created_at"]
    list_filter = ["provider_type", "is_active"]
    search_fields = ["label", "from_email", "tenant__name"]
    raw_id_fields = ["tenant"]
    readonly_fields = ["last_tested_at", "last_test_success", "last_test_message"]


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "tenant", "is_active", "created_at"]
    list_filter = ["is_active", "tenant"]
    search_fields = ["name", "slug", "subject"]
    raw_id_fields = ["tenant"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = [
        "template_slug", "recipient_email", "status",
        "sent_at", "opened_at", "clicked_at", "created_at",
    ]
    list_filter = ["status", "template_slug"]
    search_fields = ["recipient_email", "template_slug", "subject"]
    raw_id_fields = ["tenant", "template", "sequence_enrollment"]
    readonly_fields = [
        "id", "tenant", "template", "template_slug",
        "recipient_email", "subject", "body_html", "status",
        "error_message", "context", "scheduled_at", "sent_at",
        "idempotency_key", "sequence_enrollment", "celery_task_id",
        "tracking_id", "opened_at", "clicked_at", "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SequenceStepInline(admin.TabularInline):
    model = SequenceStep
    extra = 1
    raw_id_fields = ["template"]


@admin.register(EmailSequence)
class EmailSequenceAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "tenant", "is_active", "created_at"]
    list_filter = ["is_active", "tenant"]
    search_fields = ["name", "slug"]
    raw_id_fields = ["tenant"]
    inlines = [SequenceStepInline]


@admin.register(SequenceEnrollment)
class SequenceEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        "recipient_email", "sequence", "status",
        "current_step", "started_at", "completed_at",
    ]
    list_filter = ["status"]
    search_fields = ["recipient_email"]
    raw_id_fields = ["tenant", "sequence"]
    readonly_fields = [
        "id", "tenant", "sequence", "recipient_email",
        "context", "status", "started_at", "completed_at",
        "current_step", "created_at",
    ]
