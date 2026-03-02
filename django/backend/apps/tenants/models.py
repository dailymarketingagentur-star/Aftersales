import uuid

from django.db import models

from apps.common.models import TimestampedModel


class Tenant(TimestampedModel):
    """Organization/Company tenant."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")

    class Meta(TimestampedModel.Meta):
        ordering = ["name"]

    def __str__(self):
        return self.name
