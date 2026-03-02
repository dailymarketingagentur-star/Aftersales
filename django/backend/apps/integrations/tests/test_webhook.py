"""Tests for webhook integration (target_type=webhook)."""

from unittest.mock import MagicMock, patch

import pytest

from apps.integrations.models import (
    ActionExecution,
    ActionSequence,
    ActionTemplate,
    ExecutionStatus,
    SequenceStep,
    StepLog,
    StepLogStatus,
)
from apps.integrations.services import IntegrationService


@pytest.fixture
def webhook_template(owner_setup):
    """Webhook template with Bearer auth."""
    tpl = ActionTemplate.objects.create(
        tenant=owner_setup,
        slug="notify-external",
        name="Externe Benachrichtigung",
        target_type="webhook",
        method="POST",
        webhook_url="https://api.example.com/hooks/{{HOOK_ID}}",
        auth_type="bearer",
        body_json={"client": "{{CLIENT_NAME}}", "event": "onboarding"},
        variables=["HOOK_ID", "CLIENT_NAME"],
        output_mapping={"id": "RESULT_ID"},
    )
    tpl.set_auth_credentials({"token": "secret-bearer-token"})
    tpl.save(update_fields=["auth_credentials_encrypted"])
    return tpl


@pytest.fixture
def webhook_template_basic(owner_setup):
    """Webhook template with Basic auth."""
    tpl = ActionTemplate.objects.create(
        tenant=owner_setup,
        slug="basic-auth-hook",
        name="Basic Auth Hook",
        target_type="webhook",
        method="POST",
        webhook_url="https://api.example.com/data",
        auth_type="basic",
        body_json={"test": True},
    )
    tpl.set_auth_credentials({"username": "user", "password": "pass"})
    tpl.save(update_fields=["auth_credentials_encrypted"])
    return tpl


@pytest.fixture
def webhook_template_apikey(owner_setup):
    """Webhook template with API Key auth."""
    tpl = ActionTemplate.objects.create(
        tenant=owner_setup,
        slug="apikey-hook",
        name="API Key Hook",
        target_type="webhook",
        method="GET",
        webhook_url="https://api.example.com/status",
        auth_type="api_key",
    )
    tpl.set_auth_credentials({"header_name": "X-API-Key", "header_value": "my-api-key"})
    tpl.save(update_fields=["auth_credentials_encrypted"])
    return tpl


@pytest.fixture
def webhook_template_noauth(owner_setup):
    """Webhook template without auth."""
    return ActionTemplate.objects.create(
        tenant=owner_setup,
        slug="noauth-hook",
        name="No Auth Hook",
        target_type="webhook",
        method="POST",
        webhook_url="https://httpbin.org/post",
        auth_type="none",
        body_json={"message": "hello"},
    )


# ---------------------------------------------------------------------------
# Model Tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestWebhookModel:
    def test_auth_credentials_roundtrip(self, webhook_template):
        creds = webhook_template.get_auth_credentials()
        assert creds == {"token": "secret-bearer-token"}

    def test_empty_credentials(self, webhook_template_noauth):
        creds = webhook_template_noauth.get_auth_credentials()
        assert creds == {}

    def test_target_type_default(self, owner_setup):
        tpl = ActionTemplate.objects.create(
            tenant=owner_setup, slug="default-type", name="Default", endpoint="/test"
        )
        assert tpl.target_type == "jira"


# ---------------------------------------------------------------------------
# _call_webhook Tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestCallWebhook:
    @patch("apps.integrations.services.requests.request")
    def test_bearer_auth(self, mock_request, owner_setup, webhook_template, user):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "result-123"}
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_resp

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=webhook_template,
            status=ExecutionStatus.RUNNING,
            input_context={"HOOK_ID": "abc", "CLIENT_NAME": "Muster GmbH"},
            triggered_by=user,
        )

        success, log = IntegrationService._call_webhook(webhook_template, execution.input_context, execution)
        assert success is True
        assert log.status == StepLogStatus.SUCCESS
        assert log.status_code == 200
        assert log.extracted_outputs == {"RESULT_ID": "result-123"}

        # Verify URL was rendered
        call_kwargs = mock_request.call_args
        assert call_kwargs.kwargs["url"] == "https://api.example.com/hooks/abc"
        # Verify Bearer header was set
        headers = call_kwargs.kwargs["headers"]
        assert headers["Authorization"] == "Bearer secret-bearer-token"

    @patch("apps.integrations.services.requests.request")
    def test_basic_auth(self, mock_request, owner_setup, webhook_template_basic, user):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_resp.headers = {}
        mock_request.return_value = mock_resp

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=webhook_template_basic,
            status=ExecutionStatus.RUNNING,
            input_context={},
            triggered_by=user,
        )

        success, log = IntegrationService._call_webhook(webhook_template_basic, {}, execution)
        assert success is True
        # Verify basic auth tuple was passed
        call_kwargs = mock_request.call_args
        assert call_kwargs.kwargs["auth"] == ("user", "pass")

    @patch("apps.integrations.services.requests.request")
    def test_api_key_auth(self, mock_request, owner_setup, webhook_template_apikey, user):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_resp.headers = {}
        mock_request.return_value = mock_resp

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=webhook_template_apikey,
            status=ExecutionStatus.RUNNING,
            input_context={},
            triggered_by=user,
        )

        success, log = IntegrationService._call_webhook(webhook_template_apikey, {}, execution)
        assert success is True
        call_kwargs = mock_request.call_args
        headers = call_kwargs.kwargs["headers"]
        assert headers["X-API-Key"] == "my-api-key"

    @patch("apps.integrations.services.requests.request")
    def test_no_auth(self, mock_request, owner_setup, webhook_template_noauth, user):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_resp.headers = {}
        mock_request.return_value = mock_resp

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=webhook_template_noauth,
            status=ExecutionStatus.RUNNING,
            input_context={},
            triggered_by=user,
        )

        success, log = IntegrationService._call_webhook(webhook_template_noauth, {}, execution)
        assert success is True
        call_kwargs = mock_request.call_args
        assert call_kwargs.kwargs["auth"] is None
        assert "Authorization" not in call_kwargs.kwargs["headers"]

    def test_unresolved_placeholders(self, owner_setup, webhook_template, user):
        """Missing variables should fail before making HTTP call."""
        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=webhook_template,
            status=ExecutionStatus.RUNNING,
            input_context={},  # HOOK_ID missing
            triggered_by=user,
        )

        success, log = IntegrationService._call_webhook(webhook_template, {}, execution)
        assert success is False
        assert log.status == StepLogStatus.FAILED
        assert "Fehlende Variablen" in log.error_message
        assert "HOOK_ID" in log.error_message

    @patch("apps.integrations.services.requests.request")
    def test_http_error(self, mock_request, owner_setup, webhook_template_noauth, user):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.json.return_value = {"error": "Internal server error"}
        mock_resp.headers = {}
        mock_request.return_value = mock_resp

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=webhook_template_noauth,
            status=ExecutionStatus.RUNNING,
            input_context={},
            triggered_by=user,
        )

        success, log = IntegrationService._call_webhook(webhook_template_noauth, {}, execution)
        assert success is False
        assert log.status == StepLogStatus.FAILED
        assert "500" in log.error_message


# ---------------------------------------------------------------------------
# run_single_action with webhook
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestRunSingleActionWebhook:
    @patch("apps.integrations.services.requests.request")
    def test_webhook_execution(self, mock_request, owner_setup, webhook_template_noauth, user):
        """Webhook execution should not require a JiraConnection."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}
        mock_resp.headers = {}
        mock_request.return_value = mock_resp

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=webhook_template_noauth,
            status=ExecutionStatus.PENDING,
            input_context={},
            triggered_by=user,
        )

        IntegrationService.run_single_action(execution)
        execution.refresh_from_db()

        assert execution.status == ExecutionStatus.COMPLETED
        assert StepLog.objects.filter(execution=execution).count() == 1


# ---------------------------------------------------------------------------
# run_sequence with mixed steps
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestRunSequenceMixed:
    @patch("apps.integrations.services.requests.request")
    def test_webhook_only_sequence(self, mock_request, owner_setup, webhook_template_noauth, user):
        """A sequence with only webhook steps should not require JiraConnection."""
        seq = ActionSequence.objects.create(
            tenant=owner_setup, slug="webhook-seq", name="Webhook Sequence"
        )
        SequenceStep.objects.create(sequence=seq, template=webhook_template_noauth, position=1)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_resp.headers = {}
        mock_request.return_value = mock_resp

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            sequence=seq,
            status=ExecutionStatus.PENDING,
            input_context={},
            triggered_by=user,
        )

        IntegrationService.run_sequence(execution)
        execution.refresh_from_db()

        assert execution.status == ExecutionStatus.COMPLETED
        assert StepLog.objects.filter(execution=execution).count() == 1

    @patch("apps.integrations.services.requests.request")
    def test_mixed_sequence_without_jira_connection(self, mock_request, owner_setup, user):
        """A mixed sequence with Jira steps should fail if no JiraConnection exists."""
        from apps.integrations.models import ActionTemplate

        jira_tpl = ActionTemplate.objects.create(
            tenant=owner_setup, slug="jira-step", name="Jira Step",
            target_type="jira", method="POST", endpoint="/rest/api/3/issue",
            body_json={"fields": {"summary": "test"}},
        )
        webhook_tpl = ActionTemplate.objects.create(
            tenant=owner_setup, slug="webhook-step", name="Webhook Step",
            target_type="webhook", method="POST", webhook_url="https://example.com/hook",
            body_json={"test": True},
        )

        seq = ActionSequence.objects.create(
            tenant=owner_setup, slug="mixed-seq", name="Mixed Sequence"
        )
        SequenceStep.objects.create(sequence=seq, template=webhook_tpl, position=1)
        SequenceStep.objects.create(sequence=seq, template=jira_tpl, position=2)

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            sequence=seq,
            status=ExecutionStatus.PENDING,
            input_context={},
            triggered_by=user,
        )

        IntegrationService.run_sequence(execution)
        execution.refresh_from_db()

        # Should fail because Jira step needs connection
        assert execution.status == ExecutionStatus.FAILED
        assert "Jira-Verbindung" in execution.error_message
