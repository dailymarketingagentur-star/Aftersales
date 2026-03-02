import pytest
from rest_framework import status

from apps.tenants.models import Tenant
from apps.users.models import Membership


@pytest.mark.django_db
class TestTenantCreate:
    def test_create_tenant(self, authenticated_client, user):
        response = authenticated_client.post(
            "/api/v1/tenants/",
            {"name": "New Agency"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Agency"
        assert response.data["slug"] == "new-agency"

        # User should be owner
        membership = Membership.objects.get(user=user, tenant_id=response.data["id"])
        assert membership.role == "owner"

    def test_create_tenant_unauthenticated(self, api_client):
        response = api_client.post(
            "/api/v1/tenants/",
            {"name": "Fail"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTenantDetail:
    def test_get_tenant(self, authenticated_client, user, tenant_factory):
        tenant = tenant_factory()
        Membership.objects.create(user=user, tenant=tenant, role="member")

        response = authenticated_client.get(
            f"/api/v1/tenants/{tenant.id}/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == tenant.name

    def test_update_tenant_as_admin(self, authenticated_client, user, tenant_factory):
        tenant = tenant_factory()
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.patch(
            f"/api/v1/tenants/{tenant.id}/",
            {"name": "Updated Name"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Name"
