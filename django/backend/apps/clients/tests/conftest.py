import pytest

from apps.clients.models import Client, ServiceType
from apps.clients.services import ServiceTypeService


@pytest.fixture
def service_type_factory(db):
    """Factory to create test service types."""

    def create_service_type(tenant, name="SEO", position=0, **kwargs):
        return ServiceType.objects.create(
            tenant=tenant,
            name=name,
            position=position,
            **kwargs,
        )

    return create_service_type


@pytest.fixture
def client_factory(db):
    """Factory to create test clients."""

    def create_client(tenant, name=None, status="active", **kwargs):
        count = Client.objects.filter(tenant=tenant).count() + 1
        if name is None:
            name = f"Test Client {count}"
        return Client.objects.create(
            tenant=tenant,
            name=name,
            status=status,
            **kwargs,
        )

    return create_client


@pytest.fixture
def seeded_tenant(tenant_factory):
    """Tenant with default service types seeded."""
    tenant = tenant_factory()
    ServiceTypeService.seed_defaults(tenant)
    return tenant
