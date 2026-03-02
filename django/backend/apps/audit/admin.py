from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ["action", "entity_type", "entity_id", "user", "tenant", "created_at"]
    list_filter = ["action", "entity_type"]
    search_fields = ["action", "entity_type", "entity_id"]
    raw_id_fields = ["user", "tenant"]
    readonly_fields = [
        "id", "tenant", "user", "action", "entity_type", "entity_id",
        "before", "after", "ip_address", "user_agent", "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
