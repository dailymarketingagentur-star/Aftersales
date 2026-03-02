from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status

from apps.integrations.models import (
    ActionExecution,
    ActionTemplate,
    ExecutionStatus,
    JiraConnection,
)
from apps.users.models import Membership


@pytest.fixture
def owner_tenant(user, tenant_factory):
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="owner")
    return tenant


@pytest.fixture
def admin_tenant(user, tenant_factory):
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="admin")
    return tenant


# ---------------------------------------------------------------------------
# Connection endpoints
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestJiraConnection:
    def test_get_no_connection(self, authenticated_client, owner_tenant):
        resp = authenticated_client.get(
            "/api/v1/integrations/connection/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_put_creates_connection(self, authenticated_client, owner_tenant):
        resp = authenticated_client.put(
            "/api/v1/integrations/connection/",
            {
                "jira_url": "https://test.atlassian.net",
                "jira_email": "user@test.com",
                "jira_api_token": "my-secret-token",
            },
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["jira_url"] == "https://test.atlassian.net"
        # Token should NOT be in the response
        assert "jira_api_token" not in resp.data
        assert "jira_api_token_encrypted" not in resp.data

    def test_put_updates_existing(self, authenticated_client, owner_tenant):
        # Create first
        authenticated_client.put(
            "/api/v1/integrations/connection/",
            {
                "jira_url": "https://old.atlassian.net",
                "jira_email": "old@test.com",
                "jira_api_token": "old-token",
            },
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        # Update
        resp = authenticated_client.put(
            "/api/v1/integrations/connection/",
            {
                "jira_url": "https://new.atlassian.net",
                "jira_email": "new@test.com",
                "jira_api_token": "new-token",
            },
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["jira_url"] == "https://new.atlassian.net"
        assert JiraConnection.objects.filter(tenant=owner_tenant, is_active=True).count() == 1

    def test_get_existing_connection(self, authenticated_client, owner_tenant):
        conn = JiraConnection(
            tenant=owner_tenant,
            jira_url="https://test.atlassian.net",
            jira_email="user@test.com",
        )
        conn.set_token("my-token")
        conn.save()

        resp = authenticated_client.get(
            "/api/v1/integrations/connection/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["jira_email"] == "user@test.com"

    def test_delete_connection(self, authenticated_client, owner_tenant):
        conn = JiraConnection(
            tenant=owner_tenant,
            jira_url="https://test.atlassian.net",
            jira_email="user@test.com",
        )
        conn.set_token("token")
        conn.save()

        resp = authenticated_client.delete(
            "/api/v1/integrations/connection/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not JiraConnection.objects.filter(tenant=owner_tenant, is_active=True).exists()

    def test_admin_cannot_manage_connection(self, authenticated_client, admin_tenant):
        resp = authenticated_client.put(
            "/api/v1/integrations/connection/",
            {
                "jira_url": "https://test.atlassian.net",
                "jira_email": "user@test.com",
                "jira_api_token": "token",
            },
            format="json",
            HTTP_X_TENANT_ID=str(admin_tenant.id),
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestConnectionTest:
    @patch("apps.integrations.services.requests.get")
    def test_successful_test(self, mock_get, authenticated_client, owner_tenant):
        conn = JiraConnection(
            tenant=owner_tenant,
            jira_url="https://test.atlassian.net",
            jira_email="user@test.com",
        )
        conn.set_token("token")
        conn.save()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"displayName": "Test User"}
        mock_get.return_value = mock_resp

        resp = authenticated_client.post(
            "/api/v1/integrations/connection/test/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["success"] is True


# ---------------------------------------------------------------------------
# Template endpoints
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestTemplates:
    def test_list_templates(self, authenticated_client, admin_tenant):
        ActionTemplate.objects.create(
            tenant=None,
            slug="system-tpl",
            name="System Template",
            method="GET",
            endpoint="/test",
            is_system=True,
        )
        ActionTemplate.objects.create(
            tenant=admin_tenant,
            slug="tenant-tpl",
            name="Tenant Template",
            method="POST",
            endpoint="/test",
        )

        resp = authenticated_client.get(
            "/api/v1/integrations/templates/",
            HTTP_X_TENANT_ID=str(admin_tenant.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 2

    def test_create_template_requires_owner(self, authenticated_client, admin_tenant):
        resp = authenticated_client.post(
            "/api/v1/integrations/templates/",
            {
                "slug": "new-tpl",
                "name": "New Template",
                "method": "POST",
                "endpoint": "/rest/api/3/issue",
            },
            format="json",
            HTTP_X_TENANT_ID=str(admin_tenant.id),
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_template_as_owner(self, authenticated_client, owner_tenant):
        resp = authenticated_client.post(
            "/api/v1/integrations/templates/",
            {
                "slug": "new-tpl",
                "name": "New Template",
                "method": "POST",
                "endpoint": "/rest/api/3/issue",
            },
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["slug"] == "new-tpl"
        assert resp.data["is_system"] is False


# ---------------------------------------------------------------------------
# Execution endpoints
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestExecution:
    @patch("apps.integrations.tasks.execute_action_task.delay")
    def test_execute_action(self, mock_delay, authenticated_client, admin_tenant):
        mock_delay.return_value = MagicMock(id="celery-123")

        ActionTemplate.objects.create(
            tenant=None,
            slug="test-action",
            name="Test Action",
            method="POST",
            endpoint="/rest/api/3/issue",
            is_system=True,
        )

        resp = authenticated_client.post(
            "/api/v1/integrations/execute/",
            {
                "template_slug": "test-action",
                "context": {"PROJECT_KEY": "TEST"},
            },
            format="json",
            HTTP_X_TENANT_ID=str(admin_tenant.id),
        )
        assert resp.status_code == status.HTTP_202_ACCEPTED
        assert resp.data["status"] == "pending"
        mock_delay.assert_called_once()

    def test_execute_unknown_template(self, authenticated_client, admin_tenant):
        resp = authenticated_client.post(
            "/api/v1/integrations/execute/",
            {"template_slug": "nonexistent"},
            format="json",
            HTTP_X_TENANT_ID=str(admin_tenant.id),
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_executions(self, authenticated_client, admin_tenant, user):
        tpl = ActionTemplate.objects.create(
            tenant=None, slug="tpl", name="T", method="GET", endpoint="/test", is_system=True,
        )
        ActionExecution.objects.create(
            tenant=admin_tenant,
            template=tpl,
            status=ExecutionStatus.COMPLETED,
            triggered_by=user,
        )
        resp = authenticated_client.get(
            "/api/v1/integrations/executions/",
            HTTP_X_TENANT_ID=str(admin_tenant.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 1

    def test_cancel_execution(self, authenticated_client, admin_tenant, user):
        tpl = ActionTemplate.objects.create(
            tenant=None, slug="tpl2", name="T2", method="GET", endpoint="/test", is_system=True,
        )
        execution = ActionExecution.objects.create(
            tenant=admin_tenant,
            template=tpl,
            status=ExecutionStatus.PENDING,
            triggered_by=user,
        )
        resp = authenticated_client.post(
            f"/api/v1/integrations/executions/{execution.id}/cancel/",
            HTTP_X_TENANT_ID=str(admin_tenant.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "cancelled"
