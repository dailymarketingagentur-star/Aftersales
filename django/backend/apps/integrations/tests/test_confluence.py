from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status

from apps.clients.models import Client, ClientKeyFact
from apps.integrations.models import ClientIntegrationData, JiraConnection, TenantIntegration
from apps.users.models import Membership


@pytest.fixture
def confluence_setup(user, tenant_factory):
    """Tenant with admin user, Jira connection, and enabled Confluence integration."""
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="admin")

    # Jira connection (Atlassian credentials)
    conn = JiraConnection(
        tenant=tenant,
        label="Test Jira",
        jira_url="https://test.atlassian.net",
        jira_email="test@example.com",
    )
    conn.set_token("test-token")
    conn.save()

    # Enable Confluence integration
    TenantIntegration.objects.create(
        tenant=tenant, integration_type="confluence", is_enabled=True, enabled_by=user,
    )

    # Create client with key facts
    client = Client.objects.create(tenant=tenant, name="Acme GmbH", status="active")
    ClientKeyFact.objects.create(tenant=tenant, client=client, label="KPI", value="CAC < 50 EUR", position=0)
    ClientKeyFact.objects.create(tenant=tenant, client=client, label="Kommunikation", value="Telefonisch", position=1)

    return {"tenant": tenant, "client": client, "conn": conn}


def _mock_response(status_code=200, json_data=None):
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.headers = {"content-type": "application/json"}
    return resp


# ---------------------------------------------------------------------------
# SyncConfluencePageView — Create
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestSyncConfluenceCreate:
    @patch("apps.integrations.views.requests")
    def test_create_page_success(self, mock_requests, authenticated_client, user, confluence_setup):
        setup = confluence_setup
        tenant, client = setup["tenant"], setup["client"]

        # Mock: GET spaces → space found
        spaces_resp = _mock_response(200, {"results": [{"id": "12345"}]})
        # Mock: POST pages → page created
        create_resp = _mock_response(200, {"id": "99999", "_links": {"webui": "/spaces/ACME/pages/99999"}})
        mock_requests.get.return_value = spaces_resp
        mock_requests.post.return_value = create_resp
        mock_requests.RequestException = Exception

        response = authenticated_client.post(
            f"/api/v1/clients/{client.slug}/integrations/confluence/sync/",
            {"space_key": "ACME"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["integration_type"] == "confluence"
        assert response.data["data"]["page_id"] == "99999"
        assert response.data["data"]["space_key"] == "ACME"

    @patch("apps.integrations.views.requests")
    def test_create_page_space_not_found(self, mock_requests, authenticated_client, user, confluence_setup):
        setup = confluence_setup
        tenant, client = setup["tenant"], setup["client"]

        spaces_resp = _mock_response(200, {"results": []})
        mock_requests.get.return_value = spaces_resp
        mock_requests.RequestException = Exception

        response = authenticated_client.post(
            f"/api/v1/clients/{client.slug}/integrations/confluence/sync/",
            {"space_key": "NOTEXIST"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_no_jira_connection(self, authenticated_client, user, tenant_factory):
        """Sync fails if no Jira connection configured."""
        tenant = tenant_factory()
        Membership.objects.create(user=user, tenant=tenant, role="admin")
        TenantIntegration.objects.create(
            tenant=tenant, integration_type="confluence", is_enabled=True, enabled_by=user,
        )
        client = Client.objects.create(tenant=tenant, name="No Jira", status="active")

        response = authenticated_client.post(
            f"/api/v1/clients/{client.slug}/integrations/confluence/sync/",
            {"space_key": "TEST"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_confluence_not_enabled(self, authenticated_client, user, confluence_setup):
        """Sync fails if Confluence integration is not enabled."""
        setup = confluence_setup
        tenant, client = setup["tenant"], setup["client"]

        # Disable Confluence
        TenantIntegration.objects.filter(tenant=tenant, integration_type="confluence").update(is_enabled=False)

        response = authenticated_client.post(
            f"/api/v1/clients/{client.slug}/integrations/confluence/sync/",
            {"space_key": "ACME"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_no_space_key(self, authenticated_client, user, confluence_setup):
        """Sync fails if no space_key provided and no Jira project linked."""
        setup = confluence_setup
        tenant, client = setup["tenant"], setup["client"]

        response = authenticated_client.post(
            f"/api/v1/clients/{client.slug}/integrations/confluence/sync/",
            {},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# SyncConfluencePageView — Update
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestSyncConfluenceUpdate:
    @patch("apps.integrations.views.requests")
    def test_update_existing_page(self, mock_requests, authenticated_client, user, confluence_setup):
        setup = confluence_setup
        tenant, client = setup["tenant"], setup["client"]

        # Pre-create confluence integration data with existing page_id
        ClientIntegrationData.objects.create(
            tenant=tenant,
            client=client,
            integration_type="confluence",
            data={"space_key": "ACME", "page_id": "88888", "page_url": "https://test.atlassian.net/wiki/spaces/ACME/pages/88888"},
        )

        # Mock: GET page → get version
        version_resp = _mock_response(200, {"version": {"number": 3}})
        # Mock: PUT page → updated
        update_resp = _mock_response(200, {"id": "88888", "_links": {"webui": "/spaces/ACME/pages/88888"}})
        mock_requests.get.return_value = version_resp
        mock_requests.put.return_value = update_resp
        mock_requests.RequestException = Exception

        response = authenticated_client.post(
            f"/api/v1/clients/{client.slug}/integrations/confluence/sync/",
            {"space_key": "ACME"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["page_id"] == "88888"

        # Verify PUT was called (update, not create)
        mock_requests.put.assert_called_once()


# ---------------------------------------------------------------------------
# ConfluenceSpacesView
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestConfluenceSpacesProxy:
    @patch("apps.integrations.views.requests")
    def test_list_spaces(self, mock_requests, authenticated_client, user, confluence_setup):
        setup = confluence_setup
        tenant = setup["tenant"]

        spaces_data = [
            {"id": "1", "key": "DEV", "name": "Development"},
            {"id": "2", "key": "MKT", "name": "Marketing"},
        ]
        mock_requests.get.return_value = _mock_response(200, {"results": spaces_data})
        mock_requests.RequestException = Exception

        response = authenticated_client.get(
            "/api/v1/integrations/confluence/spaces/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]["key"] == "DEV"

    def test_no_jira_connection(self, authenticated_client, user, tenant_factory):
        tenant = tenant_factory()
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.get(
            "/api/v1/integrations/confluence/spaces/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
