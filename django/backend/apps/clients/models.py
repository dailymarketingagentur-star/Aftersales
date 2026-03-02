from decimal import Decimal

from django.db import models
from django.utils.text import slugify

from apps.common.models import TenantScopedModel


class ServiceType(TenantScopedModel):
    """Configurable service type per tenant (e.g. SEO, SEA, Webdesign)."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, editable=False)
    is_default = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta(TenantScopedModel.Meta):
        ordering = ["position", "name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "slug"], name="unique_service_type_per_tenant"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while ServiceType.objects.filter(tenant=self.tenant, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Client(TenantScopedModel):
    """A client (Mandant) of the agency."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Aktiv"
        ONBOARDING = "onboarding", "Onboarding"
        PAUSED = "paused", "Pausiert"
        CHURNED = "churned", "Churned"

    class Tier(models.TextChoices):
        BRONZE = "bronze", "Bronze"
        SILBER = "silber", "Silber"
        GOLD = "gold", "Gold"
        PLATIN = "platin", "Platin"

    # Stammdaten
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, editable=False)
    contact_first_name = models.CharField(max_length=255, blank=True, default="")
    contact_last_name = models.CharField(max_length=255, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    contact_phone = models.CharField(max_length=50, blank=True, default="")
    website = models.URLField(blank=True, default="")
    cloud_storage_url = models.CharField(max_length=500, blank=True, default="")

    # Vertrag
    start_date = models.DateField(null=True, blank=True)
    monthly_volume = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.BRONZE)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONBOARDING)
    health_score = models.PositiveIntegerField(default=100)
    notes = models.TextField(blank=True, default="")

    class Meta(TenantScopedModel.Meta):
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "slug"], name="unique_client_per_tenant"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Client.objects.filter(tenant=self.tenant, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def recalculate_volume(self):
        """Recalculate monthly_volume from active services and update tier."""
        total = self.services.filter(status=Service.Status.ACTIVE).aggregate(
            total=models.Sum("monthly_budget")
        )["total"] or Decimal("0.00")
        self.monthly_volume = total
        self.tier = self._calculate_tier(total)
        self.save(update_fields=["monthly_volume", "tier", "updated_at"])

    @staticmethod
    def _calculate_tier(volume):
        if volume >= 10000:
            return Client.Tier.PLATIN
        elif volume >= 5000:
            return Client.Tier.GOLD
        elif volume >= 2500:
            return Client.Tier.SILBER
        return Client.Tier.BRONZE


class Service(TenantScopedModel):
    """A service (Dienstleistung) delivered to a client."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Aktiv"
        PAUSED = "paused", "Pausiert"
        COMPLETED = "completed", "Abgeschlossen"
        CANCELLED = "cancelled", "Storniert"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="services")
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT, related_name="services")
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    monthly_budget = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    link = models.URLField(max_length=500, blank=True, default="")
    description = models.TextField(blank=True, default="")

    class Meta(TenantScopedModel.Meta):
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.client.name})"


class ClientKeyFact(TenantScopedModel):
    """A key fact about a client (e.g. preferred communication, most important KPI)."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="key_facts")
    label = models.CharField(max_length=255)
    value = models.TextField()
    position = models.PositiveIntegerField(default=0)

    class Meta(TenantScopedModel.Meta):
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(fields=["client", "label"], name="unique_key_fact_per_client"),
        ]

    def __str__(self):
        return f"{self.label}: {self.value[:50]}"
