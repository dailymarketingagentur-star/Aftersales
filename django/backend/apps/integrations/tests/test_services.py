from unittest.mock import MagicMock, patch

import pytest

from apps.integrations.models import ActionExecution, ExecutionStatus, StepLog, StepLogStatus
from apps.integrations.services import IntegrationService


@pytest.mark.django_db
class TestRenderTemplate:
    def test_string_rendering(self):
        result = IntegrationService._render_template("Hello {{NAME}}", {"NAME": "World"})
        assert result == "Hello World"

    def test_dict_rendering(self):
        template = {"key": "{{PROJECT}}", "nested": {"val": "{{VALUE}}"}}
        result = IntegrationService._render_template(template, {"PROJECT": "ABC", "VALUE": "123"})
        assert result == {"key": "ABC", "nested": {"val": "123"}}

    def test_list_rendering(self):
        template = ["{{A}}", "static", "{{B}}"]
        result = IntegrationService._render_template(template, {"A": "1", "B": "2"})
        assert result == ["1", "static", "2"]

    def test_missing_variable_keeps_placeholder(self):
        result = IntegrationService._render_template("{{MISSING}}", {})
        assert result == "{{MISSING}}"

    def test_non_string_passthrough(self):
        assert IntegrationService._render_template(42, {}) == 42
        assert IntegrationService._render_template(True, {}) is True

    def test_dict_key_rendering(self):
        """Dict keys with {{PLACEHOLDER}} should also be rendered."""
        template = {"{{FIELD_ID}}": "some_value", "static_key": "{{VALUE}}"}
        result = IntegrationService._render_template(
            template, {"FIELD_ID": "customfield_10057", "VALUE": "test"}
        )
        assert result == {"customfield_10057": "some_value", "static_key": "test"}

    def test_nested_dict_key_rendering(self):
        """Nested dict keys should be rendered recursively."""
        template = {"fields": {"{{CF_EMAIL}}": "{{EMAIL}}", "summary": "Test"}}
        result = IntegrationService._render_template(
            template, {"CF_EMAIL": "customfield_10057", "EMAIL": "user@test.com"}
        )
        assert result == {"fields": {"customfield_10057": "user@test.com", "summary": "Test"}}


@pytest.mark.django_db
class TestFindUnresolved:
    def test_finds_placeholders_in_string(self):
        result = IntegrationService._find_unresolved("/api/{{PROJECT_ID}}/issue")
        assert result == {"PROJECT_ID"}

    def test_finds_in_dict_keys_and_values(self):
        result = IntegrationService._find_unresolved({"{{KEY}}": "{{VALUE}}", "ok": "fine"})
        assert result == {"KEY", "VALUE"}

    def test_finds_in_nested_structures(self):
        result = IntegrationService._find_unresolved({"fields": {"email": "{{EMAIL}}"}})
        assert result == {"EMAIL"}

    def test_no_placeholders_returns_empty(self):
        result = IntegrationService._find_unresolved("/api/project", {"key": "ABC"})
        assert result == set()

    def test_multiple_args(self):
        result = IntegrationService._find_unresolved("/api/{{A}}", {"b": "{{C}}"})
        assert result == {"A", "C"}


@pytest.mark.django_db
class TestExtractOutputs:
    def test_simple_extraction(self):
        response = {"id": "12345", "key": "PROJ-1"}
        mapping = {"id": "PROJECT_ID", "key": "PROJECT_KEY"}
        result = IntegrationService._extract_outputs(response, mapping)
        assert result == {"PROJECT_ID": "12345", "PROJECT_KEY": "PROJ-1"}

    def test_nested_extraction(self):
        response = {"data": {"user": {"name": "Test"}}}
        mapping = {"data.user.name": "USER_NAME"}
        result = IntegrationService._extract_outputs(response, mapping)
        assert result == {"USER_NAME": "Test"}

    def test_missing_path_skipped(self):
        response = {"id": "123"}
        mapping = {"nonexistent.path": "VALUE"}
        result = IntegrationService._extract_outputs(response, mapping)
        assert result == {}

    def test_empty_mapping(self):
        result = IntegrationService._extract_outputs({"id": "123"}, {})
        assert result == {}

    def test_none_response(self):
        result = IntegrationService._extract_outputs(None, {"id": "VALUE"})
        assert result == {}

    def test_array_response_index_access(self):
        """Array responses should be traversable via numeric index (e.g. '0.accountId')."""
        response = [{"accountId": "abc123", "displayName": "Test User"}]
        mapping = {"0.accountId": "LEAD_ACCOUNT_ID"}
        result = IntegrationService._extract_outputs(response, mapping)
        assert result == {"LEAD_ACCOUNT_ID": "abc123"}

    def test_array_response_nested_access(self):
        """Multiple array elements should be accessible."""
        response = [{"id": "first"}, {"id": "second"}]
        mapping = {"0.id": "FIRST_ID", "1.id": "SECOND_ID"}
        result = IntegrationService._extract_outputs(response, mapping)
        assert result == {"FIRST_ID": "first", "SECOND_ID": "second"}

    def test_array_response_out_of_bounds(self):
        """Out of bounds index should be skipped."""
        response = [{"id": "only"}]
        mapping = {"5.id": "MISSING"}
        result = IntegrationService._extract_outputs(response, mapping)
        assert result == {}


@pytest.mark.django_db
class TestResolveTemplate:
    def test_system_template_found(self, owner_setup, system_template):
        template = IntegrationService._resolve_template(owner_setup, "create-jira-issue")
        assert template is not None
        assert template.slug == "create-jira-issue"
        assert template.is_system is True

    def test_tenant_override(self, owner_setup, system_template):
        from apps.integrations.models import ActionTemplate

        # Create tenant-specific override
        ActionTemplate.objects.create(
            tenant=owner_setup,
            slug="create-jira-issue",
            name="Custom Issue Creator",
            method="POST",
            endpoint="/rest/api/3/issue",
            body_json={"custom": True},
        )
        template = IntegrationService._resolve_template(owner_setup, "create-jira-issue")
        assert template.tenant == owner_setup
        assert template.name == "Custom Issue Creator"

    def test_not_found_returns_none(self, owner_setup):
        template = IntegrationService._resolve_template(owner_setup, "nonexistent-slug")
        assert template is None


@pytest.mark.django_db
class TestTestConnection:
    @patch("apps.integrations.services.requests.get")
    def test_success(self, mock_get, jira_connection):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"displayName": "Test User", "emailAddress": "test@example.com"}
        mock_get.return_value = mock_resp

        success, message = IntegrationService.test_connection(jira_connection)
        assert success is True
        assert "Test User" in message
        jira_connection.refresh_from_db()
        assert jira_connection.last_test_success is True

    @patch("apps.integrations.services.requests.get")
    def test_failure(self, mock_get, jira_connection):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_get.return_value = mock_resp

        success, message = IntegrationService.test_connection(jira_connection)
        assert success is False
        assert "401" in message
        jira_connection.refresh_from_db()
        assert jira_connection.last_test_success is False


@pytest.mark.django_db
class TestExecute:
    @patch("apps.integrations.tasks.execute_action_task.delay")
    def test_creates_execution(self, mock_delay, owner_setup, system_template, user):
        mock_delay.return_value = MagicMock(id="celery-task-123")

        execution = IntegrationService.execute(
            tenant=owner_setup,
            template_slug="create-jira-issue",
            context={"PROJECT_KEY": "TEST", "ISSUE_SUMMARY": "Test Issue"},
            user=user,
            entity_type="client",
            entity_id="test-uuid",
        )

        assert execution.status == ExecutionStatus.PENDING
        assert execution.template == system_template
        assert execution.input_context["PROJECT_KEY"] == "TEST"
        assert execution.triggered_by == user
        mock_delay.assert_called_once()

    @patch("apps.integrations.tasks.execute_action_task.delay")
    def test_idempotency(self, mock_delay, owner_setup, system_template, user):
        mock_delay.return_value = MagicMock(id="task-1")

        exec1 = IntegrationService.execute(
            tenant=owner_setup,
            template_slug="create-jira-issue",
            context={},
            user=user,
            idempotency_key="unique-key-123",
        )
        exec2 = IntegrationService.execute(
            tenant=owner_setup,
            template_slug="create-jira-issue",
            context={},
            user=user,
            idempotency_key="unique-key-123",
        )
        assert exec1.id == exec2.id
        assert mock_delay.call_count == 1

    def test_unknown_template_raises(self, owner_setup, user):
        with pytest.raises(ValueError, match="nicht gefunden"):
            IntegrationService.execute(
                tenant=owner_setup,
                template_slug="nonexistent",
                user=user,
            )


@pytest.mark.django_db
class TestRunSingleAction:
    @patch("apps.integrations.services.requests.request")
    def test_successful_execution(self, mock_request, owner_setup, jira_connection, system_template, user):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"id": "10001", "key": "TEST-1"}
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_resp

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=system_template,
            status=ExecutionStatus.PENDING,
            input_context={"PROJECT_KEY": "TEST", "ISSUE_SUMMARY": "My Issue"},
            triggered_by=user,
        )

        IntegrationService.run_single_action(execution)
        execution.refresh_from_db()

        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.accumulated_context["ISSUE_ID"] == "10001"
        assert execution.accumulated_context["ISSUE_KEY"] == "TEST-1"

        logs = StepLog.objects.filter(execution=execution)
        assert logs.count() == 1
        assert logs.first().status == StepLogStatus.SUCCESS
        assert logs.first().status_code == 201

    @patch("apps.integrations.services.requests.request")
    def test_failed_execution(self, mock_request, owner_setup, jira_connection, system_template, user):
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"errorMessages": ["Bad request"]}
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_resp

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=system_template,
            status=ExecutionStatus.PENDING,
            input_context={"PROJECT_KEY": "TEST", "ISSUE_SUMMARY": "Fail"},
            triggered_by=user,
        )

        IntegrationService.run_single_action(execution)
        execution.refresh_from_db()

        assert execution.status == ExecutionStatus.FAILED
        logs = StepLog.objects.filter(execution=execution)
        assert logs.first().status == StepLogStatus.FAILED

    def test_no_connection_fails(self, owner_setup, system_template, user):
        """Without a JiraConnection, execution should fail gracefully."""
        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=system_template,
            status=ExecutionStatus.PENDING,
            input_context={},
            triggered_by=user,
        )

        IntegrationService.run_single_action(execution)
        execution.refresh_from_db()

        assert execution.status == ExecutionStatus.FAILED
        assert "Keine aktive Jira-Verbindung" in execution.error_message

    def test_missing_variables_blocks_call(self, owner_setup, jira_connection, system_template, user):
        """Execution should fail with clear message when required variables are missing."""
        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=system_template,
            status=ExecutionStatus.PENDING,
            input_context={},  # PROJECT_KEY and ISSUE_SUMMARY missing
            triggered_by=user,
        )

        IntegrationService.run_single_action(execution)
        execution.refresh_from_db()

        assert execution.status == ExecutionStatus.FAILED
        assert "Fehlende Variablen" in execution.error_message
        # Should mention the missing variable names
        assert "PROJECT_KEY" in execution.error_message or "ISSUE_SUMMARY" in execution.error_message
        # No HTTP call should have been made
        logs = StepLog.objects.filter(execution=execution)
        assert logs.count() == 1
        assert logs.first().status == StepLogStatus.FAILED
        assert logs.first().status_code is None  # No HTTP call was made

    @patch("apps.integrations.services.requests.request")
    def test_config_auto_injection(self, mock_request, owner_setup, jira_connection, system_template, user):
        """Connection config should be auto-injected into context, with input_context taking priority."""
        # Set config on the connection
        jira_connection.config = {"ISSUE_TYPE_ID": "10123", "PROJECT_KEY": "DEFAULT"}
        jira_connection.save(update_fields=["config"])

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"id": "10001", "key": "CUSTOM-1"}
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_resp

        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=system_template,
            status=ExecutionStatus.PENDING,
            # PROJECT_KEY in input_context should override config's DEFAULT
            input_context={"PROJECT_KEY": "CUSTOM", "ISSUE_SUMMARY": "Test"},
            triggered_by=user,
        )

        IntegrationService.run_single_action(execution)
        execution.refresh_from_db()

        assert execution.status == ExecutionStatus.COMPLETED
        # Verify the request was made — the rendered body should use CUSTOM (from input) not DEFAULT (from config)
        call_kwargs = mock_request.call_args
        body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert body["fields"]["project"]["key"] == "CUSTOM"


@pytest.mark.django_db
class TestCancelExecution:
    def test_cancel_pending(self, owner_setup, system_template, user):
        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=system_template,
            status=ExecutionStatus.PENDING,
            triggered_by=user,
        )
        result = IntegrationService.cancel_execution(execution)
        assert result.status == ExecutionStatus.CANCELLED

    def test_cancel_completed_noop(self, owner_setup, system_template, user):
        execution = ActionExecution.objects.create(
            tenant=owner_setup,
            template=system_template,
            status=ExecutionStatus.COMPLETED,
            triggered_by=user,
        )
        result = IntegrationService.cancel_execution(execution)
        assert result.status == ExecutionStatus.COMPLETED
