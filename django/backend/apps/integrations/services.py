"""Integration service layer.

Public API for other apps:
    IntegrationService.execute(tenant, "create-jira-issue", context={...}, user=user)
    IntegrationService.start_sequence(tenant, "client-onboarding", context={...}, user=user)
"""

import re
import time
import uuid

import requests
import structlog
from django.utils import timezone

from apps.audit.services import AuditService

logger = structlog.get_logger()


class IntegrationService:
    """Facade for executing Jira actions and sequences."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def execute(tenant, template_slug, context=None, user=None, entity_type="", entity_id="", idempotency_key=""):
        """Execute a single action template asynchronously.

        Returns the ActionExecution instance (status=pending).
        The actual HTTP call happens in a Celery task.
        """
        from apps.integrations.models import ActionExecution, ExecutionStatus
        from apps.integrations.tasks import execute_action_task

        template = IntegrationService._resolve_template(tenant, template_slug)
        if not template:
            raise ValueError(f"Template '{template_slug}' nicht gefunden.")

        if idempotency_key:
            existing = ActionExecution.objects.filter(
                tenant=tenant, idempotency_key=idempotency_key
            ).first()
            if existing:
                return existing

        execution = ActionExecution.objects.create(
            tenant=tenant,
            template=template,
            status=ExecutionStatus.PENDING,
            input_context=context or {},
            triggered_by=user,
            entity_type=entity_type,
            entity_id=str(entity_id),
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )

        task = execute_action_task.delay(str(execution.id))
        execution.celery_task_id = task.id
        execution.save(update_fields=["celery_task_id"])

        AuditService.log(
            tenant=tenant,
            user=user,
            action="integration.execute",
            entity_type="integration_execution",
            entity_id=str(execution.id),
            after={"template": template_slug, "context": context or {}},
        )

        return execution

    @staticmethod
    def start_sequence(tenant, sequence_slug, context=None, user=None, entity_type="", entity_id="", idempotency_key=""):
        """Start a sequence execution asynchronously.

        Returns the ActionExecution instance (status=pending).
        Steps are executed one-by-one in a Celery task with output forwarding.
        """
        from apps.integrations.models import ActionExecution, ActionSequence, ExecutionStatus
        from apps.integrations.tasks import execute_sequence_task

        sequence = IntegrationService._resolve_sequence(tenant, sequence_slug)
        if not sequence:
            raise ValueError(f"Sequence '{sequence_slug}' nicht gefunden.")

        if idempotency_key:
            existing = ActionExecution.objects.filter(
                tenant=tenant, idempotency_key=idempotency_key
            ).first()
            if existing:
                return existing

        execution = ActionExecution.objects.create(
            tenant=tenant,
            sequence=sequence,
            status=ExecutionStatus.PENDING,
            input_context=context or {},
            triggered_by=user,
            entity_type=entity_type,
            entity_id=str(entity_id),
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )

        task = execute_sequence_task.delay(str(execution.id))
        execution.celery_task_id = task.id
        execution.save(update_fields=["celery_task_id"])

        AuditService.log(
            tenant=tenant,
            user=user,
            action="integration.start_sequence",
            entity_type="integration_execution",
            entity_id=str(execution.id),
            after={"sequence": sequence_slug, "context": context or {}},
        )

        return execution

    @staticmethod
    def cancel_execution(execution):
        """Cancel a pending or running execution."""
        from apps.integrations.models import ExecutionStatus

        if execution.status in (ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED):
            return execution

        execution.status = ExecutionStatus.CANCELLED
        execution.save(update_fields=["status", "updated_at"])
        return execution

    @staticmethod
    def test_connection(connection):
        """Test a Jira connection by calling /rest/api/3/myself. Returns (success, message)."""
        try:
            token = connection.get_token()
            resp = requests.get(
                f"{connection.jira_url.rstrip('/')}/rest/api/3/myself",
                auth=(connection.jira_email, token),
                headers={"Accept": "application/json"},
                timeout=10,
            )
            connection.last_tested_at = timezone.now()
            connection.last_test_success = resp.status_code == 200
            connection.save(update_fields=["last_tested_at", "last_test_success"])

            if resp.status_code == 200:
                data = resp.json()
                return True, f"Verbunden als {data.get('displayName', data.get('emailAddress', '?'))}"
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
        except requests.RequestException as e:
            connection.last_tested_at = timezone.now()
            connection.last_test_success = False
            connection.save(update_fields=["last_tested_at", "last_test_success"])
            return False, str(e)

    # ------------------------------------------------------------------
    # Step execution (called by Celery tasks)
    # ------------------------------------------------------------------

    @staticmethod
    def run_single_action(execution):
        """Execute a single template action (synchronous, called from Celery)."""
        from apps.integrations.models import ExecutionStatus

        execution.status = ExecutionStatus.RUNNING
        execution.save(update_fields=["status"])

        template = execution.template

        if template.target_type == "webhook":
            context = {**execution.input_context}
            success, log = IntegrationService._call_webhook(template, context, execution, position=0)
        else:
            connection = IntegrationService._get_connection(execution.tenant)
            if not connection:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = "Keine aktive Jira-Verbindung konfiguriert."
                execution.save(update_fields=["status", "error_message"])
                return
            # Tenant-Config als Basis, input_context ueberschreibt
            context = {**getattr(connection, "config", {}), **execution.input_context}
            success, log = IntegrationService._call_jira(connection, template, context, execution, position=0)

        if success:
            execution.status = ExecutionStatus.COMPLETED
            execution.accumulated_context = {**context, **log.extracted_outputs}
        else:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = log.error_message
        execution.save(update_fields=["status", "error_message", "accumulated_context"])

    @staticmethod
    def run_sequence(execution):
        """Execute all steps of a sequence (synchronous, called from Celery).

        Supports mixed sequences with Jira and Webhook steps.
        """
        from apps.integrations.models import ExecutionStatus

        execution.status = ExecutionStatus.RUNNING
        execution.save(update_fields=["status"])

        steps = execution.sequence.steps.filter(is_active=True).select_related("template").order_by("position")

        # Pruefen ob mindestens ein Jira-Step dabei ist
        has_jira_steps = any(s.template.target_type == "jira" for s in steps)
        connection = None
        if has_jira_steps:
            connection = IntegrationService._get_connection(execution.tenant)
            if not connection:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = "Keine aktive Jira-Verbindung konfiguriert."
                execution.save(update_fields=["status", "error_message"])
                return

        # Tenant-Config als Basis (falls Jira-Connection vorhanden), input_context ueberschreibt
        base_config = getattr(connection, "config", {}) if connection else {}
        context = {**base_config, **execution.input_context}

        for step in steps:
            # Check for cancellation between steps
            execution.refresh_from_db(fields=["status"])
            if execution.status == ExecutionStatus.CANCELLED:
                return

            if step.delay_seconds > 0:
                time.sleep(step.delay_seconds)

            execution.current_step = step.position
            execution.save(update_fields=["current_step"])

            # Webhook oder Jira je nach target_type des Templates
            if step.template.target_type == "webhook":
                success, log = IntegrationService._call_webhook(
                    step.template, context, execution, position=step.position
                )
            else:
                success, log = IntegrationService._call_jira(
                    connection, step.template, context, execution, position=step.position
                )

            if success:
                # Forward outputs to context for next steps
                context.update(log.extracted_outputs)
                execution.accumulated_context = context
                execution.save(update_fields=["accumulated_context"])
            else:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = f"Step {step.position} ({step.template.slug}) fehlgeschlagen: {log.error_message}"
                execution.save(update_fields=["status", "error_message"])
                return

        execution.status = ExecutionStatus.COMPLETED
        execution.save(update_fields=["status"])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_template(tenant, slug):
        """Resolve a template: tenant-specific first, then system fallback."""
        from apps.integrations.models import ActionTemplate

        # Tenant override
        tpl = ActionTemplate.objects.filter(tenant=tenant, slug=slug, is_active=True).first()
        if tpl:
            return tpl
        # System fallback
        return ActionTemplate.objects.filter(tenant__isnull=True, slug=slug, is_active=True).first()

    @staticmethod
    def _resolve_sequence(tenant, slug):
        """Resolve a sequence: tenant-specific first, then system fallback."""
        from apps.integrations.models import ActionSequence

        seq = ActionSequence.objects.filter(tenant=tenant, slug=slug, is_active=True).first()
        if seq:
            return seq
        return ActionSequence.objects.filter(tenant__isnull=True, slug=slug, is_active=True).first()

    @staticmethod
    def _get_connection(tenant):
        """Get the active Jira connection for a tenant."""
        from apps.integrations.models import JiraConnection

        return JiraConnection.objects.filter(tenant=tenant, is_active=True).first()

    @staticmethod
    def _render_template(value, context):
        """Replace {{PLACEHOLDER}} with values from context.

        Works on strings, dicts, and lists (recursive).
        """
        if isinstance(value, str):
            def replacer(match):
                key = match.group(1).strip()
                return str(context.get(key, match.group(0)))
            return re.sub(r"\{\{(\w+)\}\}", replacer, value)
        elif isinstance(value, dict):
            return {
                IntegrationService._render_template(k, context): IntegrationService._render_template(v, context)
                for k, v in value.items()
            }
        elif isinstance(value, list):
            return [IntegrationService._render_template(item, context) for item in value]
        return value

    @staticmethod
    def _find_unresolved(*values) -> set[str]:
        """Find any remaining {{PLACEHOLDER}} in rendered strings, dicts, or lists."""
        unresolved: set[str] = set()

        def _scan(value):
            if isinstance(value, str):
                unresolved.update(re.findall(r"\{\{(\w+)\}\}", value))
            elif isinstance(value, dict):
                for k, v in value.items():
                    _scan(k)
                    _scan(v)
            elif isinstance(value, list):
                for item in value:
                    _scan(item)

        for val in values:
            _scan(val)
        return unresolved

    @staticmethod
    def _extract_outputs(response_json, output_mapping):
        """Extract values from a JSON response using simple dot-path notation.

        output_mapping example: {"id": "PROJECT_ID", "key": "PROJECT_KEY"}
        Maps response field paths to variable names.
        """
        outputs = {}
        if not output_mapping or response_json is None:
            return outputs

        for json_path, variable_name in output_mapping.items():
            value = response_json
            try:
                for part in json_path.split("."):
                    if isinstance(value, dict):
                        value = value[part]
                    elif isinstance(value, list) and part.isdigit():
                        value = value[int(part)]
                    else:
                        value = None
                        break
                if value is not None:
                    outputs[variable_name] = value
            except (KeyError, IndexError, TypeError):
                continue

        return outputs

    @staticmethod
    def _call_webhook(template, context, execution, position=0):
        """Make a Webhook HTTP call. Returns (success, StepLog)."""
        from apps.integrations.models import StepLog, StepLogStatus

        rendered_url = IntegrationService._render_template(template.webhook_url, context)
        rendered_body = IntegrationService._render_template(template.body_json, context) if template.body_json else {}
        rendered_headers = IntegrationService._render_template(template.headers_json, context) if template.headers_json else {}

        # Pruefen ob noch unaufgeloeste Platzhalter vorhanden sind
        unresolved = IntegrationService._find_unresolved(rendered_url, rendered_body)
        if unresolved:
            names = ", ".join(sorted(unresolved))
            error_msg = f"Fehlende Variablen: {names}. Bitte Platzhalter-Werte vervollstaendigen."
            log = StepLog.objects.create(
                tenant=execution.tenant,
                execution=execution,
                template=template,
                position=position,
                method=template.method,
                url="",
                request_body=rendered_body,
                status=StepLogStatus.FAILED,
                error_message=error_msg,
            )
            return False, log

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            **rendered_headers,
        }

        # Auth anwenden
        auth = None
        try:
            creds = template.get_auth_credentials()
            if template.auth_type == "bearer" and creds.get("token"):
                headers["Authorization"] = f"Bearer {creds['token']}"
            elif template.auth_type == "basic" and creds.get("username"):
                auth = (creds["username"], creds.get("password", ""))
            elif template.auth_type == "api_key" and creds.get("header_name"):
                headers[creds["header_name"]] = creds.get("header_value", "")
        except Exception as e:
            log = StepLog.objects.create(
                tenant=execution.tenant,
                execution=execution,
                template=template,
                position=position,
                method=template.method,
                url=rendered_url,
                request_body=rendered_body,
                status=StepLogStatus.FAILED,
                error_message=f"Auth-Credentials konnten nicht entschluesselt werden: {e}",
            )
            return False, log

        # Auth-Token aus geloggten Headers entfernen
        safe_headers = {k: ("***" if k.lower() == "authorization" else v) for k, v in headers.items()}

        start_time = time.monotonic()
        try:
            resp = requests.request(
                method=template.method,
                url=rendered_url,
                auth=auth,
                headers=headers,
                json=rendered_body if template.method in ("POST", "PUT") else None,
                timeout=30,
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)

            try:
                response_body = resp.json()
            except (ValueError, requests.exceptions.JSONDecodeError):
                response_body = {"raw": resp.text[:2000]}

            response_headers = dict(resp.headers)

            is_success = 200 <= resp.status_code < 300
            extracted = {}
            if is_success:
                extracted = IntegrationService._extract_outputs(response_body, template.output_mapping)

            error_msg = ""
            if not is_success:
                if resp.status_code == 401:
                    error_msg = "Webhook-Authentifizierung fehlgeschlagen (HTTP 401). Credentials prüfen."
                elif resp.status_code == 403:
                    error_msg = "Keine Berechtigung für diesen Webhook (HTTP 403)."
                elif resp.status_code == 404:
                    error_msg = f"Webhook-URL nicht gefunden: {rendered_url}"
                else:
                    error_msg = f"Webhook-Fehler (HTTP {resp.status_code})"

            log = StepLog.objects.create(
                tenant=execution.tenant,
                execution=execution,
                template=template,
                position=position,
                method=template.method,
                url=rendered_url,
                request_body=rendered_body,
                request_headers=safe_headers,
                status_code=resp.status_code,
                response_body=response_body,
                response_headers=response_headers,
                status=StepLogStatus.SUCCESS if is_success else StepLogStatus.FAILED,
                error_message=error_msg,
                extracted_outputs=extracted,
                duration_ms=duration_ms,
            )

            return is_success, log

        except requests.RequestException as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            log = StepLog.objects.create(
                tenant=execution.tenant,
                execution=execution,
                template=template,
                position=position,
                method=template.method,
                url=rendered_url,
                request_body=rendered_body,
                request_headers=safe_headers,
                status=StepLogStatus.FAILED,
                error_message=str(e),
                duration_ms=duration_ms,
            )
            return False, log

    @staticmethod
    def _call_jira(connection, template, context, execution, position=0):
        """Make an actual Jira API call. Returns (success, StepLog)."""
        from apps.integrations.models import StepLog, StepLogStatus

        rendered_endpoint = IntegrationService._render_template(template.endpoint, context)
        rendered_body = IntegrationService._render_template(template.body_json, context) if template.body_json else {}
        rendered_headers = IntegrationService._render_template(template.headers_json, context) if template.headers_json else {}

        # Pruefen ob noch unaufgeloeste Platzhalter vorhanden sind
        unresolved = IntegrationService._find_unresolved(rendered_endpoint, rendered_body)
        if unresolved:
            names = ", ".join(sorted(unresolved))
            error_msg = f"Fehlende Variablen: {names}. Bitte Stammdaten des Mandanten vervollstaendigen."
            log = StepLog.objects.create(
                tenant=execution.tenant,
                execution=execution,
                template=template,
                position=position,
                method=template.method,
                url="",
                request_body=rendered_body,
                status=StepLogStatus.FAILED,
                error_message=error_msg,
            )
            return False, log

        url = f"{connection.jira_url.rstrip('/')}{rendered_endpoint}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            **rendered_headers,
        }

        # Redact token from logged headers
        safe_headers = {k: v for k, v in headers.items()}

        start_time = time.monotonic()
        try:
            token = connection.get_token()
            resp = requests.request(
                method=template.method,
                url=url,
                auth=(connection.jira_email, token),
                headers=headers,
                json=rendered_body if template.method in ("POST", "PUT") else None,
                timeout=30,
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)

            try:
                response_body = resp.json()
            except (ValueError, requests.exceptions.JSONDecodeError):
                response_body = {"raw": resp.text[:2000]}

            response_headers = dict(resp.headers)

            is_success = 200 <= resp.status_code < 300
            extracted = {}
            if is_success:
                extracted = IntegrationService._extract_outputs(response_body, template.output_mapping)

            # Klartext-Fehlermeldungen statt kryptischer HTTP-Codes
            error_msg = ""
            if not is_success:
                if resp.status_code == 401:
                    error_msg = (
                        "Jira API-Token ist ungültig oder abgelaufen. "
                        "Bitte erneuere den Token unter Integrationen → Jira → Verbindung."
                    )
                elif resp.status_code == 403:
                    error_msg = (
                        "Keine Berechtigung für diese Jira-Aktion. "
                        "Prüfe ob der API-Token die nötigen Rechte hat."
                    )
                elif resp.status_code == 404:
                    error_msg = f"Jira-Ressource nicht gefunden: {rendered_endpoint}"
                else:
                    error_msg = f"Jira API-Fehler (HTTP {resp.status_code})"

            log = StepLog.objects.create(
                tenant=execution.tenant,
                execution=execution,
                template=template,
                position=position,
                method=template.method,
                url=url,
                request_body=rendered_body,
                request_headers=safe_headers,
                status_code=resp.status_code,
                response_body=response_body,
                response_headers=response_headers,
                status=StepLogStatus.SUCCESS if is_success else StepLogStatus.FAILED,
                error_message=error_msg,
                extracted_outputs=extracted,
                duration_ms=duration_ms,
            )

            return is_success, log

        except requests.RequestException as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            log = StepLog.objects.create(
                tenant=execution.tenant,
                execution=execution,
                template=template,
                position=position,
                method=template.method,
                url=url,
                request_body=rendered_body,
                request_headers=safe_headers,
                status=StepLogStatus.FAILED,
                error_message=str(e),
                duration_ms=duration_ms,
            )
            return False, log
