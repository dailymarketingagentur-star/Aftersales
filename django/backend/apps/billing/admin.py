from django.contrib import admin

from .models import TenantSubscription


@admin.register(TenantSubscription)
class TenantSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["tenant", "status", "plan_name", "current_period_end", "created_at"]
    list_filter = ["status"]
    search_fields = ["tenant__name", "stripe_subscription_id"]
    raw_id_fields = ["tenant"]
    readonly_fields = ["id", "created_at", "updated_at"]
