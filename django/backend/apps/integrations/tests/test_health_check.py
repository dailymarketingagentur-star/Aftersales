from unittest.mock import MagicMock, patch

import pytest

from apps.emails.models import EmailProviderConnection, EmailProviderType
from apps.integrations.models import JiraConnection
from apps.integrations.tasks import check_all_jira_connections, _notify_owner_connection_failed
from apps.users.models import Membership


@pytest.mark.django_db
class TestCheckAllJiraConnections:
    @patch("apps.integrations.services.requests.get")
    def test_healthy_connection(self, mock_get, owner_setup):
        """Healthy connection: last_test_success stays True, no email sent."""
        conn = JiraConnection(
            tenant=owner_setup,
            jira_url="https://test.atlassian.net",
            jira_email="test@example.com",
        )
        conn.set_token("valid-token")
        conn.save()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"displayName": "Test User"}
        mock_get.return_value = mock_resp

        result = check_all_jira_connections()

        assert result["tested"] == 1
        assert result["failed"] == 0
        conn.refresh_from_db()
        assert conn.last_test_success is True

    @patch("apps.integrations.tasks._notify_owner_connection_failed")
    @patch("apps.integrations.services.requests.get")
    def test_failed_connection_sends_notification(self, mock_get, mock_notify, owner_setup):
        """First failure triggers notification to owner."""
        conn = JiraConnection(
            tenant=owner_setup,
            jira_url="https://test.atlassian.net",
            jira_email="test@example.com",
            last_test_success=True,  # was healthy before
        )
        conn.set_token("expired-token")
        conn.save()

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_get.return_value = mock_resp

        result = check_all_jira_connections()

        assert result["tested"] == 1
        assert result["failed"] == 1
        conn.refresh_from_db()
        assert conn.last_test_success is False
        mock_notify.assert_called_once()

    @patch("apps.integrations.tasks._notify_owner_connection_failed")
    @patch("apps.integrations.services.requests.get")
    def test_already_failed_no_duplicate_notification(self, mock_get, mock_notify, owner_setup):
        """Already-failed connection doesn't send a second notification."""
        conn = JiraConnection(
            tenant=owner_setup,
            jira_url="https://test.atlassian.net",
            jira_email="test@example.com",
            last_test_success=False,  # already failed
        )
        conn.set_token("still-expired")
        conn.save()

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_get.return_value = mock_resp

        result = check_all_jira_connections()

        assert result["failed"] == 1
        mock_notify.assert_not_called()  # no duplicate email

    @patch("apps.integrations.services.requests.get")
    def test_no_connections_returns_zero(self, mock_get):
        """No connections at all: tested=0, failed=0."""
        result = check_all_jira_connections()
        assert result["tested"] == 0
        assert result["failed"] == 0
        mock_get.assert_not_called()


@pytest.mark.django_db
class TestNotifyOwner:
    @patch("apps.integrations.tasks.EmailMultiAlternatives")
    def test_sends_email_to_owner(self, mock_email_cls, owner_setup, user):
        # Create active email provider for the tenant
        EmailProviderConnection.objects.create(
            tenant=owner_setup,
            provider_type=EmailProviderType.SMTP,
            label="Test SMTP",
            from_email="noreply@example.com",
            smtp_host="smtp.example.com",
            smtp_port=587,
            is_active=True,
        )

        conn = JiraConnection(
            tenant=owner_setup,
            jira_url="https://test.atlassian.net",
            jira_email="test@example.com",
        )
        conn.set_token("token")
        conn.save()

        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg

        _notify_owner_connection_failed(conn, "HTTP 401: Unauthorized")

        mock_email_cls.assert_called_once()
        call_kwargs = mock_email_cls.call_args[1]
        assert user.email in call_kwargs["to"]
        assert "abgelaufen" in call_kwargs["body"]
        assert "API-Token" in call_kwargs["body"]
        mock_msg.send.assert_called_once()

    def test_skips_when_no_email_provider(self, owner_setup, user):
        """No active email provider: notification is skipped (not sent)."""
        conn = JiraConnection(
            tenant=owner_setup,
            jira_url="https://test.atlassian.net",
            jira_email="test@example.com",
        )
        conn.set_token("token")
        conn.save()

        # Should not raise, just log
        _notify_owner_connection_failed(conn, "HTTP 401: Unauthorized")

    def test_no_owner_no_email(self, tenant_factory):
        """Tenant without an owner membership: no email sent."""
        tenant = tenant_factory()
        # No membership created
        conn = JiraConnection(
            tenant=tenant,
            jira_url="https://test.atlassian.net",
            jira_email="test@example.com",
        )
        conn.set_token("token")
        conn.save()

        _notify_owner_connection_failed(conn, "error")


@pytest.mark.django_db
class TestClarityErrorMessages:
    """Verify that _call_jira produces clear German error messages for common HTTP errors."""

    @patch("apps.integrations.services.requests.request")
    def test_401_produces_token_expired_message(self, mock_request, owner_setup, jira_connection, user):
        from apps.integrations.models import ActionExecution, ActionTemplate, ExecutionStatus, StepLog
        from apps.integrations.services import IntegrationService

        template = ActionTemplate.objects.create(
            tenant=None,
            slug="test-401",
            name="Test 401",
            method="GET",
            endpoint="/rest/api/3/myself",
            is_system=True,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"message": "Unauthorized"}
        mock_resp.headers = {}
        mock_request.return_value = mock_resp

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=template,
            status=ExecutionStatus.PENDING,
            triggered_by=user,
        )

        IntegrationService.run_single_action(execution)
        execution.refresh_from_db()

        assert execution.status == ExecutionStatus.FAILED
        log = StepLog.objects.filter(execution=execution).first()
        assert "API-Token" in log.error_message
        assert "abgelaufen" in log.error_message
        assert "Verbindung" in log.error_message
