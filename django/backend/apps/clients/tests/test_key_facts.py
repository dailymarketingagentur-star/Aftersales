import pytest
from rest_framework import status

from apps.clients.models import Client, ClientKeyFact
from apps.users.models import Membership


@pytest.fixture
def _setup(user, tenant_factory):
    """Tenant with subscription, user as admin, and a test client."""
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="admin")
    client = Client.objects.create(tenant=tenant, name="Test GmbH", status="active")
    return tenant, client


# ---------------------------------------------------------------------------
# Key-Fact List + Create
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestKeyFactListCreate:
    def test_list_empty(self, authenticated_client, user, _setup):
        tenant, client = _setup
        response = authenticated_client.get(
            f"/api/v1/clients/{client.slug}/key-facts/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_create_key_fact(self, authenticated_client, user, _setup):
        tenant, client = _setup
        response = authenticated_client.post(
            f"/api/v1/clients/{client.slug}/key-facts/",
            {"label": "Bevorzugte Kommunikation", "value": "Telefonisch"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["label"] == "Bevorzugte Kommunikation"
        assert response.data["value"] == "Telefonisch"
        assert response.data["position"] == 0

    def test_list_returns_created(self, authenticated_client, user, _setup):
        tenant, client = _setup
        ClientKeyFact.objects.create(
            tenant=tenant, client=client, label="KPI", value="CAC < 50 EUR", position=0,
        )
        ClientKeyFact.objects.create(
            tenant=tenant, client=client, label="Kanal", value="Google Ads", position=1,
        )
        response = authenticated_client.get(
            f"/api/v1/clients/{client.slug}/key-facts/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        # Ordered by position
        assert response.data[0]["label"] == "KPI"
        assert response.data[1]["label"] == "Kanal"

    def test_create_duplicate_label_fails(self, authenticated_client, user, _setup):
        tenant, client = _setup
        ClientKeyFact.objects.create(
            tenant=tenant, client=client, label="KPI", value="CAC", position=0,
        )
        response = authenticated_client.post(
            f"/api/v1/clients/{client.slug}/key-facts/",
            {"label": "KPI", "value": "LTV"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_client_not_found(self, authenticated_client, user, _setup):
        tenant, _ = _setup
        response = authenticated_client.get(
            "/api/v1/clients/nonexistent/key-facts/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Key-Fact Detail (PATCH, DELETE)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestKeyFactDetail:
    def test_patch_key_fact(self, authenticated_client, user, _setup):
        tenant, client = _setup
        kf = ClientKeyFact.objects.create(
            tenant=tenant, client=client, label="KPI", value="CAC", position=0,
        )
        response = authenticated_client.patch(
            f"/api/v1/clients/{client.slug}/key-facts/{kf.id}/",
            {"value": "LTV > 500 EUR"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["value"] == "LTV > 500 EUR"
        assert response.data["label"] == "KPI"

    def test_delete_key_fact(self, authenticated_client, user, _setup):
        tenant, client = _setup
        kf = ClientKeyFact.objects.create(
            tenant=tenant, client=client, label="KPI", value="CAC", position=0,
        )
        response = authenticated_client.delete(
            f"/api/v1/clients/{client.slug}/key-facts/{kf.id}/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ClientKeyFact.objects.filter(id=kf.id).exists()

    def test_delete_not_found(self, authenticated_client, user, _setup):
        tenant, client = _setup
        response = authenticated_client.delete(
            f"/api/v1/clients/{client.slug}/key-facts/00000000-0000-0000-0000-000000000000/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Permission: Member can read, but not write
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestKeyFactPermissions:
    def test_member_can_read(self, authenticated_client, user, tenant_factory):
        tenant = tenant_factory()
        Membership.objects.create(user=user, tenant=tenant, role="member")
        client = Client.objects.create(tenant=tenant, name="Perm Test", status="active")
        ClientKeyFact.objects.create(
            tenant=tenant, client=client, label="K", value="V", position=0,
        )
        response = authenticated_client.get(
            f"/api/v1/clients/{client.slug}/key-facts/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK

    def test_member_cannot_create(self, authenticated_client, user, tenant_factory):
        tenant = tenant_factory()
        Membership.objects.create(user=user, tenant=tenant, role="member")
        client = Client.objects.create(tenant=tenant, name="Perm Test", status="active")
        response = authenticated_client.post(
            f"/api/v1/clients/{client.slug}/key-facts/",
            {"label": "X", "value": "Y"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
