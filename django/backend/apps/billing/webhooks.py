import structlog
from django.dispatch import receiver

logger = structlog.get_logger()

try:
    from djstripe import webhooks as djstripe_webhooks
    from djstripe.models import Subscription

    @djstripe_webhooks.handler("customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted")
    def handle_subscription_event(event, **kwargs):
        """Sync subscription status when Stripe sends webhook events."""
        from apps.billing.models import TenantSubscription
        from apps.tenants.models import Tenant

        stripe_sub = event.data.get("object", {})
        customer_id = stripe_sub.get("customer", "")

        try:
            tenant = Tenant.objects.get(stripe_customer_id=customer_id)
        except Tenant.DoesNotExist:
            logger.warning("webhook_tenant_not_found", customer_id=customer_id)
            return

        sub, _ = TenantSubscription.objects.get_or_create(tenant=tenant)
        sub.stripe_subscription_id = stripe_sub.get("id", "")
        sub.status = stripe_sub.get("status", "none")
        sub.current_period_end = stripe_sub.get("current_period_end")

        items = stripe_sub.get("items", {}).get("data", [])
        if items:
            sub.plan_name = items[0].get("price", {}).get("nickname", "") or ""

        sub.save()

        logger.info(
            "subscription_synced",
            tenant_id=str(tenant.id),
            status=sub.status,
            event_type=event.type,
        )
except ImportError:
    pass
