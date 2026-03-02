from django.contrib import admin

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


@admin.register(JiraConnection)
class JiraConnectionAdmin(admin.ModelAdmin):
    list_display = ["label", "tenant", "jira_url", "is_active", "last_tested_at", "last_test_success"]
    list_filter = ["is_active", "last_test_success"]
    search_fields = ["label", "jira_url", "jira_email"]
    raw_id_fields = ["tenant"]
    readonly_fields = ["last_tested_at", "last_test_success"]
    exclude = ["jira_api_token_encrypted"]


@admin.register(ActionTemplate)
class ActionTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "tenant", "target_type", "method", "endpoint", "is_system", "is_active", "created_at"]
    list_filter = ["is_active", "is_system", "method", "target_type", "tenant"]
    search_fields = ["name", "slug", "endpoint", "webhook_url"]
    raw_id_fields = ["tenant"]
    prepopulated_fields = {"slug": ("name",)}
    exclude = ["auth_credentials_encrypted"]


class IntegrationStepInline(admin.TabularInline):
    model = SequenceStep
    extra = 1
    raw_id_fields = ["template"]


@admin.register(ActionSequence)
class ActionSequenceAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "tenant", "is_active", "created_at"]
    list_filter = ["is_active", "tenant"]
    search_fields = ["name", "slug"]
    raw_id_fields = ["tenant"]
    inlines = [IntegrationStepInline]


@admin.register(ActionExecution)
class ActionExecutionAdmin(admin.ModelAdmin):
    list_display = ["__str__", "tenant", "status", "entity_type", "entity_id", "triggered_by", "created_at"]
    list_filter = ["status", "entity_type"]
    search_fields = ["entity_id", "idempotency_key"]
    raw_id_fields = ["tenant", "sequence", "template", "triggered_by"]
    readonly_fields = [
        "id", "tenant", "sequence", "template", "status",
        "input_context", "accumulated_context", "current_step",
        "error_message", "triggered_by", "entity_type", "entity_id",
        "celery_task_id", "idempotency_key", "created_at", "updated_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StepLog)
class StepLogAdmin(admin.ModelAdmin):
    list_display = ["__str__", "tenant", "method", "status_code", "status", "duration_ms", "created_at"]
    list_filter = ["status", "method"]
    search_fields = ["url"]
    raw_id_fields = ["tenant", "execution", "template"]
    readonly_fields = [
        "id", "tenant", "execution", "template", "position",
        "method", "url", "request_body", "request_headers",
        "status_code", "response_body", "response_headers",
        "status", "error_message", "extracted_outputs",
        "duration_ms", "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TwilioConnection)
class TwilioConnectionAdmin(admin.ModelAdmin):
    list_display = ["label", "tenant", "account_sid", "phone_number", "is_active", "last_tested_at", "last_test_success"]
    list_filter = ["is_active", "last_test_success"]
    search_fields = ["label", "account_sid", "phone_number"]
    raw_id_fields = ["tenant"]
    readonly_fields = ["last_tested_at", "last_test_success"]
    exclude = ["auth_token_encrypted"]


@admin.register(TenantIntegration)
class TenantIntegrationAdmin(admin.ModelAdmin):
    list_display = ["integration_type", "tenant", "is_enabled", "enabled_by", "created_at"]
    list_filter = ["is_enabled", "integration_type"]
    search_fields = ["integration_type", "tenant__name"]
    raw_id_fields = ["tenant", "enabled_by"]


@admin.register(ClientIntegrationData)
class ClientIntegrationDataAdmin(admin.ModelAdmin):
    list_display = ["client", "integration_type", "tenant", "created_at", "updated_at"]
    list_filter = ["integration_type"]
    search_fields = ["client__name", "integration_type"]
    raw_id_fields = ["tenant", "client"]
