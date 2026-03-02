import pytest

from apps.clients.models import Client, ServiceType
from apps.clients.services import ClientService, ServiceTypeService


@pytest.mark.django_db
class TestServiceTypeService:
    def test_seed_defaults(self, tenant_factory):
        tenant = tenant_factory()
        created = ServiceTypeService.seed_defaults(tenant)
        assert created == 7
        assert ServiceType.objects.filter(tenant=tenant).count() == 7

    def test_seed_defaults_idempotent(self, tenant_factory):
        tenant = tenant_factory()
        ServiceTypeService.seed_defaults(tenant)
        created = ServiceTypeService.seed_defaults(tenant)
        assert created == 0
        assert ServiceType.objects.filter(tenant=tenant).count() == 7

    def test_seed_defaults_creates_expected_types(self, tenant_factory):
        tenant = tenant_factory()
        ServiceTypeService.seed_defaults(tenant)
        slugs = set(ServiceType.objects.filter(tenant=tenant).values_list("slug", flat=True))
        assert "seo" in slugs
        assert "seagoogle-ads" in slugs
        assert "social-media" in slugs
        assert "webdesign" in slugs
        assert "content-marketing" in slugs
        assert "e-mail-marketing" in slugs
        assert "beratungconsulting" in slugs


@pytest.mark.django_db
class TestClientService:
    def test_create_client(self, tenant_factory, user_factory):
        tenant = tenant_factory()
        user = user_factory()
        client = ClientService.create_client(
            tenant=tenant,
            data={"name": "New Client", "contact_email": "test@example.com"},
            user=user,
        )
        assert client.name == "New Client"
        assert client.slug == "new-client"
        assert client.tenant == tenant

    def test_update_client(self, tenant_factory, user_factory):
        tenant = tenant_factory()
        user = user_factory()
        client = Client.objects.create(tenant=tenant, name="Old Name")

        updated = ClientService.update_client(
            client, {"name": "New Name", "status": "active"}, user
        )
        assert updated.name == "New Name"
        assert updated.status == "active"

    def test_soft_delete_client(self, tenant_factory, user_factory):
        tenant = tenant_factory()
        user = user_factory()
        client = Client.objects.create(tenant=tenant, name="To Delete", status="active")

        deleted = ClientService.soft_delete_client(client, user)
        assert deleted.status == "churned"

        client.refresh_from_db()
        assert client.status == "churned"
