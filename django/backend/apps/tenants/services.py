import structlog
from django.db import transaction
from django.utils.text import slugify

logger = structlog.get_logger()


class TenantService:
    @staticmethod
    @transaction.atomic
    def create_tenant(name, owner_user):
        """Create a new tenant and assign the creating user as owner."""
        from apps.tenants.models import Tenant
        from apps.users.models import Membership
        from apps.audit.services import AuditService

        slug = slugify(name)
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        tenant = Tenant.objects.create(name=name, slug=slug)

        # Auto-create free subscription so tenant can use the platform
        from apps.billing.models import TenantSubscription

        TenantSubscription.objects.create(
            tenant=tenant,
            status=TenantSubscription.Status.FREE,
            plan_name="Free",
        )

        Membership.objects.create(
            user=owner_user,
            tenant=tenant,
            role="owner",
        )

        AuditService.log(
            tenant=tenant,
            user=owner_user,
            action="tenant.created",
            entity_type="tenant",
            entity_id=str(tenant.id),
            after={"name": name, "slug": slug},
        )

        # Seed default service types
        from apps.clients.services import ServiceTypeService
        ServiceTypeService.seed_defaults(tenant)

        logger.info("tenant_created", tenant_id=str(tenant.id), name=name, owner=str(owner_user.id))
        return tenant

    @staticmethod
    def update_tenant(tenant, data, user):
        """Update tenant details."""
        from apps.audit.services import AuditService

        before = {"name": tenant.name, "slug": tenant.slug}

        for key, value in data.items():
            if hasattr(tenant, key) and key not in ("id", "created_at", "updated_at"):
                setattr(tenant, key, value)
        tenant.save()

        AuditService.log(
            tenant=tenant,
            user=user,
            action="tenant.updated",
            entity_type="tenant",
            entity_id=str(tenant.id),
            before=before,
            after=data,
        )

        return tenant
