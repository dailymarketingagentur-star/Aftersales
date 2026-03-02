import structlog
import stripe
from django.conf import settings

logger = structlog.get_logger()


class BillingService:
    @staticmethod
    def create_checkout_session(tenant, price_id, success_url, cancel_url):
        """Create a Stripe Checkout session for the tenant."""
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY if not settings.STRIPE_LIVE_MODE else settings.STRIPE_LIVE_SECRET_KEY

        if not tenant.stripe_customer_id:
            customer = stripe.Customer.create(
                name=tenant.name,
                metadata={"tenant_id": str(tenant.id)},
            )
            tenant.stripe_customer_id = customer.id
            tenant.save()

        session = stripe.checkout.Session.create(
            customer=tenant.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"tenant_id": str(tenant.id)},
        )

        logger.info("checkout_session_created", tenant_id=str(tenant.id), session_id=session.id)
        return session

    @staticmethod
    def create_portal_session(tenant, return_url):
        """Create a Stripe Billing Portal session."""
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY if not settings.STRIPE_LIVE_MODE else settings.STRIPE_LIVE_SECRET_KEY

        if not tenant.stripe_customer_id:
            return None

        session = stripe.billing_portal.Session.create(
            customer=tenant.stripe_customer_id,
            return_url=return_url,
        )
        return session

    @staticmethod
    def sync_subscription_status(tenant):
        """Sync subscription status from Stripe."""
        from apps.billing.models import TenantSubscription

        sub, _ = TenantSubscription.objects.get_or_create(tenant=tenant)

        if not tenant.stripe_customer_id:
            # No Stripe customer — return current status without overwriting
            return sub

        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY if not settings.STRIPE_LIVE_MODE else settings.STRIPE_LIVE_SECRET_KEY

        subscriptions = stripe.Subscription.list(
            customer=tenant.stripe_customer_id,
            limit=1,
            status="all",
        )

        if subscriptions.data:
            stripe_sub = subscriptions.data[0]
            sub.stripe_subscription_id = stripe_sub.id
            sub.status = stripe_sub.status
            sub.current_period_end = stripe_sub.current_period_end
            if stripe_sub.items.data:
                sub.plan_name = stripe_sub.items.data[0].price.nickname or ""
        else:
            sub.status = TenantSubscription.Status.NONE

        sub.save()
        return sub
