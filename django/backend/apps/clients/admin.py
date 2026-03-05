from django.contrib import admin

from apps.clients.models import ChurnWarningAssessment, Client, ClientEmailAddress, ClientPhoneNumber, HealthScoreAssessment, Service, ServiceType


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0
    fields = ["name", "service_type", "status", "monthly_budget", "start_date", "end_date"]
    raw_id_fields = ["service_type"]


class ClientPhoneNumberInline(admin.TabularInline):
    model = ClientPhoneNumber
    extra = 0
    fields = ["label", "number", "position"]


class ClientEmailAddressInline(admin.TabularInline):
    model = ClientEmailAddress
    extra = 0
    fields = ["label", "email", "position"]


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "tenant", "is_default", "position", "created_at"]
    list_filter = ["is_default"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "slug", "created_at", "updated_at"]
    raw_id_fields = ["tenant"]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "tenant", "status", "tier", "monthly_volume", "health_score", "created_at"]
    list_filter = ["status", "tier"]
    search_fields = ["name", "slug", "contact_email"]
    readonly_fields = ["id", "slug", "monthly_volume", "tier", "created_at", "updated_at"]
    raw_id_fields = ["tenant"]
    inlines = [ServiceInline, ClientPhoneNumberInline, ClientEmailAddressInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "client", "service_type", "status", "monthly_budget", "created_at"]
    list_filter = ["status"]
    search_fields = ["name", "client__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["tenant", "client", "service_type"]


@admin.register(HealthScoreAssessment)
class HealthScoreAssessmentAdmin(admin.ModelAdmin):
    list_display = ["client", "total_score", "status_label", "assessed_by", "created_at"]
    list_filter = ["total_score"]
    readonly_fields = ["id", "total_score", "created_at", "updated_at"]
    raw_id_fields = ["tenant", "client", "task", "assessed_by"]


@admin.register(ChurnWarningAssessment)
class ChurnWarningAssessmentAdmin(admin.ModelAdmin):
    list_display = ["client", "active_signals", "assessed_by", "created_at"]
    readonly_fields = ["id", "active_signals", "created_at", "updated_at"]
    raw_id_fields = ["tenant", "client", "task", "assessed_by"]
