"""Tests for the tenant integration types and client integration data features."""

from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status as http_status

from apps.clients.models import Client
from apps.integrations.models import ClientIntegrationData, JiraConnection, TenantIntegration
from apps.integrations.registry import INTEGRATION_TYPES
from apps.users.models import Membership


@pytest.fixture
def member_setup(user, tenant_factory):
    """Tenant with user as member (read-only)."""
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="member")
    return tenant


@pytest.fixture
def admin_tenant(user, tenant_factory):
    """Tenant with user as admin."""
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="admin")
    return tenant


@pytest.fixture
def owner_tenant(user, tenant_factory):
    """Tenant with user as owner."""
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="owner")
    return tenant


@pytest.fixture
def test_client(owner_tenant):
    """A test client scoped to the owner's tenant."""
    return Client.objects.create(tenant=owner_tenant, name="Test Mandant")


# ---------------------------------------------------------------------------
# Integration Types
# ---------------------------------------------------------------------------
class TestIntegrationTypes:
    def test_list_types_returns_all_registry_types(self, authenticated_client, member_setup):
        resp = authenticated_client.get(
            "/api/v1/integrations/types/",
            HTTP_X_TENANT_ID=str(member_setup.id),
        )
        assert resp.status_code == http_status.HTTP_200_OK
        keys = {t["key"] for t in resp.data}
        assert keys == set(INTEGRATION_TYPES.keys())

    def test_list_types_shows_enabled_status(self, authenticated_client, owner_tenant):
        TenantIntegration.objects.create(
            tenant=owner_tenant, integration_type="jira", is_enabled=True
        )
        resp = authenticated_client.get(
            "/api/v1/integrations/types/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_200_OK
        jira = next(t for t in resp.data if t["key"] == "jira")
        hubspot = next(t for t in resp.data if t["key"] == "hubspot")
        assert jira["is_enabled"] is True
        assert hubspot["is_enabled"] is False

    def test_list_types_includes_field_definitions(self, authenticated_client, member_setup):
        resp = authenticated_client.get(
            "/api/v1/integrations/types/",
            HTTP_X_TENANT_ID=str(member_setup.id),
        )
        jira = next(t for t in resp.data if t["key"] == "jira")
        field_keys = {f["key"] for f in jira["fields"]}
        assert "project_url" in field_keys
        assert "project_key" in field_keys


# ---------------------------------------------------------------------------
# Integration Toggle
# ---------------------------------------------------------------------------
class TestIntegrationToggle:
    def test_enable_integration(self, authenticated_client, owner_tenant):
        resp = authenticated_client.post(
            "/api/v1/integrations/toggle/",
            {"integration_type": "jira", "is_enabled": True},
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data["is_enabled"] is True
        assert TenantIntegration.objects.filter(
            tenant=owner_tenant, integration_type="jira", is_enabled=True
        ).exists()

    def test_disable_integration(self, authenticated_client, owner_tenant):
        TenantIntegration.objects.create(
            tenant=owner_tenant, integration_type="jira", is_enabled=True
        )
        resp = authenticated_client.post(
            "/api/v1/integrations/toggle/",
            {"integration_type": "jira", "is_enabled": False},
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data["is_enabled"] is False

    def test_toggle_requires_owner(self, authenticated_client, member_setup):
        resp = authenticated_client.post(
            "/api/v1/integrations/toggle/",
            {"integration_type": "jira", "is_enabled": True},
            format="json",
            HTTP_X_TENANT_ID=str(member_setup.id),
        )
        assert resp.status_code == http_status.HTTP_403_FORBIDDEN

    def test_toggle_invalid_type(self, authenticated_client, owner_tenant):
        resp = authenticated_client.post(
            "/api/v1/integrations/toggle/",
            {"integration_type": "invalid_type", "is_enabled": True},
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Client Integration Data
# ---------------------------------------------------------------------------
class TestClientIntegrationData:
    def test_get_empty_data(self, authenticated_client, owner_tenant, test_client):
        TenantIntegration.objects.create(
            tenant=owner_tenant, integration_type="jira", is_enabled=True
        )
        resp = authenticated_client.get(
            f"/api/v1/clients/{test_client.slug}/integrations/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data == []

    def test_put_without_enabled_integration(self, authenticated_client, owner_tenant, test_client):
        resp = authenticated_client.put(
            f"/api/v1/clients/{test_client.slug}/integrations/",
            {
                "integration_type": "jira",
                "data": {"project_url": "https://test.atlassian.net/browse/TEST"},
            },
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_put_with_enabled_integration(self, authenticated_client, owner_tenant, test_client):
        TenantIntegration.objects.create(
            tenant=owner_tenant, integration_type="jira", is_enabled=True
        )
        data = {
            "project_url": "https://test.atlassian.net/browse/TEST",
            "project_key": "TEST",
        }
        resp = authenticated_client.put(
            f"/api/v1/clients/{test_client.slug}/integrations/",
            {"integration_type": "jira", "data": data},
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_201_CREATED
        assert resp.data["data"]["project_url"] == data["project_url"]
        assert resp.data["data"]["project_key"] == data["project_key"]

    def test_put_invalid_fields(self, authenticated_client, owner_tenant, test_client):
        TenantIntegration.objects.create(
            tenant=owner_tenant, integration_type="jira", is_enabled=True
        )
        resp = authenticated_client.put(
            f"/api/v1/clients/{test_client.slug}/integrations/",
            {"integration_type": "jira", "data": {"invalid_field": "value"}},
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_get_only_returns_enabled(self, authenticated_client, owner_tenant, test_client):
        """Data for disabled integrations should not appear in GET."""
        ti = TenantIntegration.objects.create(
            tenant=owner_tenant, integration_type="jira", is_enabled=True
        )
        ClientIntegrationData.objects.create(
            tenant=owner_tenant,
            client=test_client,
            integration_type="jira",
            data={"project_key": "TEST"},
        )
        # With enabled: data shows up
        resp = authenticated_client.get(
            f"/api/v1/clients/{test_client.slug}/integrations/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert len(resp.data) == 1

        # Disable → data hidden
        ti.is_enabled = False
        ti.save()
        resp = authenticated_client.get(
            f"/api/v1/clients/{test_client.slug}/integrations/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert len(resp.data) == 0

    def test_update_existing_data(self, authenticated_client, owner_tenant, test_client):
        TenantIntegration.objects.create(
            tenant=owner_tenant, integration_type="jira", is_enabled=True
        )
        ClientIntegrationData.objects.create(
            tenant=owner_tenant,
            client=test_client,
            integration_type="jira",
            data={"project_key": "OLD"},
        )
        resp = authenticated_client.put(
            f"/api/v1/clients/{test_client.slug}/integrations/",
            {"integration_type": "jira", "data": {"project_key": "NEW"}},
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data["data"]["project_key"] == "NEW"
        assert ClientIntegrationData.objects.filter(client=test_client).count() == 1


# ---------------------------------------------------------------------------
# Create Jira Project
# ---------------------------------------------------------------------------
class TestCreateJiraProject:
    @pytest.fixture
    def jira_setup(self, owner_tenant, test_client):
        """Enable Jira integration and create a JiraConnection."""
        TenantIntegration.objects.create(
            tenant=owner_tenant, integration_type="jira", is_enabled=True
        )
        conn = JiraConnection(
            tenant=owner_tenant,
            label="Jira Cloud",
            jira_url="https://test.atlassian.net",
            jira_email="test@example.com",
            is_active=True,
        )
        conn.set_token("test-api-token")
        conn.save()
        return conn

    @patch("apps.integrations.views.requests.post")
    @patch("apps.integrations.views.requests.get")
    def test_create_project_success(
        self, mock_get, mock_post, authenticated_client, owner_tenant, test_client, jira_setup
    ):
        # Mock GET /myself
        myself_resp = MagicMock()
        myself_resp.status_code = 200
        myself_resp.json.return_value = {"accountId": "abc123"}
        mock_get.return_value = myself_resp

        # Mock POST /project
        create_resp = MagicMock()
        create_resp.status_code = 201
        create_resp.headers = {"content-type": "application/json"}
        create_resp.json.return_value = {"id": "10001", "key": "TM"}
        mock_post.return_value = create_resp

        resp = authenticated_client.post(
            f"/api/v1/clients/{test_client.slug}/integrations/jira/create-project/",
            {"project_name": "Test Mandant", "project_key": "TM"},
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_201_CREATED
        assert resp.data["data"]["project_key"] == "TM"
        assert resp.data["data"]["project_id"] == "10001"
        assert "test.atlassian.net/browse/TM" in resp.data["data"]["project_url"]

    def test_create_project_no_connection(self, authenticated_client, owner_tenant, test_client):
        """Without a JiraConnection → 404."""
        TenantIntegration.objects.create(
            tenant=owner_tenant, integration_type="jira", is_enabled=True
        )
        resp = authenticated_client.post(
            f"/api/v1/clients/{test_client.slug}/integrations/jira/create-project/",
            {"project_name": "Test", "project_key": "TS"},
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_404_NOT_FOUND

    def test_create_project_already_linked(self, authenticated_client, owner_tenant, test_client, jira_setup):
        """If project_key is already set → 409."""
        ClientIntegrationData.objects.create(
            tenant=owner_tenant,
            client=test_client,
            integration_type="jira",
            data={"project_key": "OLD", "project_id": "999"},
        )
        resp = authenticated_client.post(
            f"/api/v1/clients/{test_client.slug}/integrations/jira/create-project/",
            {"project_name": "Test", "project_key": "TS"},
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_409_CONFLICT

    def test_create_project_invalid_key(self, authenticated_client, owner_tenant, test_client, jira_setup):
        """Invalid project_key → 400."""
        resp = authenticated_client.post(
            f"/api/v1/clients/{test_client.slug}/integrations/jira/create-project/",
            {"project_name": "Test", "project_key": "invalid"},
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST
