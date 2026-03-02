import structlog
from django.db import transaction
from django.utils.text import slugify

logger = structlog.get_logger()

DEFAULT_SERVICE_TYPES = [
    {"name": "SEO", "position": 1},
    {"name": "SEA/Google Ads", "position": 2},
    {"name": "Social Media", "position": 3},
    {"name": "Webdesign", "position": 4},
    {"name": "Content Marketing", "position": 5},
    {"name": "E-Mail Marketing", "position": 6},
    {"name": "Beratung/Consulting", "position": 7},
]


class ClientService:
    @staticmethod
    @transaction.atomic
    def create_client(tenant, data, user):
        """Create a new client for the tenant."""
        from apps.audit.services import AuditService
        from apps.clients.models import Client

        client = Client(tenant=tenant, **data)
        client.save()

        AuditService.log(
            tenant=tenant,
            user=user,
            action="client.created",
            entity_type="client",
            entity_id=str(client.id),
            after={"name": client.name, "slug": client.slug},
        )

        logger.info("client_created", client_id=str(client.id), tenant_id=str(tenant.id))
        return client

    @staticmethod
    @transaction.atomic
    def update_client(client, data, user):
        """Update client details."""
        from apps.audit.services import AuditService

        before = {"name": client.name, "status": client.status}

        for key, value in data.items():
            if hasattr(client, key) and key not in ("id", "slug", "tenant", "created_at", "updated_at"):
                setattr(client, key, value)
        client.save()

        AuditService.log(
            tenant=client.tenant,
            user=user,
            action="client.updated",
            entity_type="client",
            entity_id=str(client.id),
            before=before,
            after=data,
        )

        return client

    @staticmethod
    @transaction.atomic
    def soft_delete_client(client, user):
        """Soft-delete a client by setting status to churned."""
        from apps.audit.services import AuditService

        before = {"status": client.status}
        client.status = "churned"
        client.save(update_fields=["status", "updated_at"])

        AuditService.log(
            tenant=client.tenant,
            user=user,
            action="client.deleted",
            entity_type="client",
            entity_id=str(client.id),
            before=before,
            after={"status": "churned"},
        )

        return client


class ServiceTypeService:
    @staticmethod
    def seed_defaults(tenant):
        """Seed default service types for a tenant."""
        from apps.clients.models import ServiceType

        created_count = 0
        for st_data in DEFAULT_SERVICE_TYPES:
            slug = slugify(st_data["name"])
            _, created = ServiceType.objects.get_or_create(
                tenant=tenant,
                slug=slug,
                defaults={
                    "name": st_data["name"],
                    "position": st_data["position"],
                    "is_default": True,
                },
            )
            if created:
                created_count += 1

        logger.info("service_types_seeded", tenant_id=str(tenant.id), created=created_count)
        return created_count
