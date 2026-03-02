from decimal import Decimal

import pytest
from rest_framework import status

from apps.clients.models import Client, Service, ServiceType
from apps.clients.services import ServiceTypeService
from apps.users.models import Membership


@pytest.fixture
def _setup(user, tenant_factory):
    """Standard setup: tenant with subscription, user as admin, service types seeded."""
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="admin")
    ServiceTypeService.seed_defaults(tenant)
    return tenant


# ---------------------------------------------------------------------------
# Client endpoints
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestClientListCreate:
    def test_list_clients(self, authenticated_client, user, _setup):
        tenant = _setup
        Client.objects.create(tenant=tenant, name="Client A", status="active")
        Client.objects.create(tenant=tenant, name="Client B", status="onboarding")

        response = authenticated_client.get(
            "/api/v1/clients/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_list_clients_filter_status(self, authenticated_client, user, _setup):
        tenant = _setup
        Client.objects.create(tenant=tenant, name="Active", status="active")
        Client.objects.create(tenant=tenant, name="Paused", status="paused")

        response = authenticated_client.get(
            "/api/v1/clients/?status=active",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Active"

    def test_list_clients_search(self, authenticated_client, user, _setup):
        tenant = _setup
        Client.objects.create(tenant=tenant, name="Alpha Corp")
        Client.objects.create(tenant=tenant, name="Beta GmbH")

        response = authenticated_client.get(
            "/api/v1/clients/?search=alpha",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_client(self, authenticated_client, user, _setup):
        tenant = _setup
        response = authenticated_client.post(
            "/api/v1/clients/",
            {"name": "New Mandant", "contact_email": "info@mandant.de"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Mandant"
        assert response.data["slug"] == "new-mandant"

    def test_create_client_unauthenticated(self, api_client):
        response = api_client.post(
            "/api/v1/clients/",
            {"name": "Fail"},
            format="json",
        )
        # TenantMiddleware returns 400 (missing X-Tenant-ID) before auth check
        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.django_db
class TestClientDetail:
    def test_get_client(self, authenticated_client, user, _setup):
        tenant = _setup
        client = Client.objects.create(tenant=tenant, name="Detail Test")

        response = authenticated_client.get(
            f"/api/v1/clients/{client.slug}/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Detail Test"

    def test_update_client(self, authenticated_client, user, _setup):
        tenant = _setup
        client = Client.objects.create(tenant=tenant, name="Old Name")

        response = authenticated_client.patch(
            f"/api/v1/clients/{client.slug}/",
            {"name": "Updated Name"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Name"

    def test_delete_client_soft(self, authenticated_client, user, _setup):
        tenant = _setup
        client = Client.objects.create(tenant=tenant, name="To Delete", status="active")

        response = authenticated_client.delete(
            f"/api/v1/clients/{client.slug}/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        client.refresh_from_db()
        assert client.status == "churned"

    def test_get_client_not_found(self, authenticated_client, user, _setup):
        tenant = _setup
        response = authenticated_client.get(
            "/api/v1/clients/nonexistent/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Service endpoints
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestServiceListCreate:
    def test_list_services(self, authenticated_client, user, _setup):
        tenant = _setup
        client = Client.objects.create(tenant=tenant, name="SVC Client")
        st = ServiceType.objects.filter(tenant=tenant).first()
        Service.objects.create(
            tenant=tenant, client=client, service_type=st,
            name="SEO Campaign", monthly_budget=Decimal("2000"),
        )

        response = authenticated_client.get(
            f"/api/v1/clients/{client.slug}/services/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_service(self, authenticated_client, user, _setup):
        tenant = _setup
        client = Client.objects.create(tenant=tenant, name="SVC Client 2")
        st = ServiceType.objects.filter(tenant=tenant).first()

        response = authenticated_client.post(
            f"/api/v1/clients/{client.slug}/services/",
            {
                "service_type": str(st.id),
                "name": "New SEO Campaign",
                "monthly_budget": "3000.00",
            },
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New SEO Campaign"

        # Verify volume recalculation
        client.refresh_from_db()
        assert client.monthly_volume == Decimal("3000.00")
        assert client.tier == Client.Tier.SILBER


@pytest.mark.django_db
class TestServiceDetail:
    def test_update_service(self, authenticated_client, user, _setup):
        tenant = _setup
        client = Client.objects.create(tenant=tenant, name="Update SVC")
        st = ServiceType.objects.filter(tenant=tenant).first()
        service = Service.objects.create(
            tenant=tenant, client=client, service_type=st,
            name="Old SVC", monthly_budget=Decimal("1000"),
        )

        response = authenticated_client.patch(
            f"/api/v1/clients/{client.slug}/services/{service.id}/",
            {"name": "Updated SVC", "monthly_budget": "5000.00"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated SVC"

    def test_delete_service(self, authenticated_client, user, _setup):
        tenant = _setup
        client = Client.objects.create(tenant=tenant, name="Delete SVC")
        st = ServiceType.objects.filter(tenant=tenant).first()
        service = Service.objects.create(
            tenant=tenant, client=client, service_type=st,
            name="To Delete", monthly_budget=Decimal("2000"),
        )

        response = authenticated_client.delete(
            f"/api/v1/clients/{client.slug}/services/{service.id}/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Service.objects.filter(pk=service.id).exists()


# ---------------------------------------------------------------------------
# ServiceType endpoints
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestServiceTypeListCreate:
    def test_list_service_types(self, authenticated_client, user, _setup):
        tenant = _setup

        response = authenticated_client.get(
            "/api/v1/service-types/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 7  # 7 defaults seeded

    def test_create_service_type(self, authenticated_client, user, _setup):
        tenant = _setup

        response = authenticated_client.post(
            "/api/v1/service-types/",
            {"name": "TikTok Ads", "position": 8},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "TikTok Ads"
        assert response.data["slug"] == "tiktok-ads"


@pytest.mark.django_db
class TestServiceTypeDetail:
    def test_update_service_type(self, authenticated_client, user, _setup):
        tenant = _setup
        st = ServiceType.objects.filter(tenant=tenant).first()

        response = authenticated_client.patch(
            f"/api/v1/service-types/{st.id}/",
            {"name": "SEO Premium"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "SEO Premium"

    def test_delete_service_type_unused(self, authenticated_client, user, _setup):
        tenant = _setup
        st = ServiceType.objects.create(tenant=tenant, name="Unused Type", position=99)

        response = authenticated_client.delete(
            f"/api/v1/service-types/{st.id}/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_service_type_in_use(self, authenticated_client, user, _setup):
        tenant = _setup
        st = ServiceType.objects.filter(tenant=tenant).first()
        client = Client.objects.create(tenant=tenant, name="Blocker")
        Service.objects.create(
            tenant=tenant, client=client, service_type=st, name="Blocking Service",
        )

        response = authenticated_client.delete(
            f"/api/v1/service-types/{st.id}/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_409_CONFLICT
