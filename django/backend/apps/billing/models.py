from django.db import models

from apps.common.models import TimestampedModel


class TenantSubscription(TimestampedModel):
    """Cached subscription status for a tenant."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        TRIALING = "trialing", "Trialing"
        FREE = "free", "Free"
        PAST_DUE = "past_due", "Past Due"
        CANCELED = "canceled", "Canceled"
        INCOMPLETE = "incomplete", "Incomplete"
        NONE = "none", "No Subscription"

    tenant = models.OneToOneField(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    stripe_subscription_id = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NONE,
    )
    current_period_end = models.DateTimeField(null=True, blank=True)
    plan_name = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"{self.tenant.name} - {self.status}"

    @property
    def is_active(self):
        return self.status in (self.Status.ACTIVE, self.Status.TRIALING, self.Status.FREE)
