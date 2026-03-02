from django.contrib import admin

from apps.clients.models import Client, Service, ServiceType


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0
    fields = ["name", "service_type", "status", "monthly_budget", "start_date", "end_date"]
    raw_id_fields = ["service_type"]


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
    inlines = [ServiceInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "client", "service_type", "status", "monthly_budget", "created_at"]
    list_filter = ["status"]
    search_fields = ["name", "client__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["tenant", "client", "service_type"]
