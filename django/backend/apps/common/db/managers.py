from django.db import models


class TenantAwareManager(models.Manager):
    """Manager that auto-filters by tenant_id."""

    def for_tenant(self, tenant):
        return self.get_queryset().filter(tenant=tenant)

    def for_tenant_id(self, tenant_id):
        return self.get_queryset().filter(tenant_id=tenant_id)
