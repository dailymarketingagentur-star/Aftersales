"""Celery tasks for async Jira integration execution."""

import structlog
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = structlog.get_logger()


@shared_task(bind=True, max_retries=2)
def execute_action_task(self, execution_id):
    """Execute a single action template."""
    from apps.integrations.models import ActionExecution, ExecutionStatus
    from apps.integrations.services import IntegrationService

    try:
        execution = ActionExecution.objects.select_related("tenant", "template").get(id=execution_id)
    except ActionExecution.DoesNotExist:
        logger.error("execution_not_found", execution_id=execution_id)
        return

    if execution.status in (ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED):
        logger.info("execution_skipped", execution_id=execution_id, status=execution.status)
        return

    try:
        IntegrationService.run_single_action(execution)
        logger.info(
            "action_executed",
            execution_id=execution_id,
            template=execution.template.slug if execution.template else "?",
            status=execution.status,
        )
    except Exception as exc:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = str(exc)
        execution.save(update_fields=["status", "error_message"])
        logger.error("action_execution_failed", execution_id=execution_id, error=str(exc))


@shared_task(bind=True, max_retries=0)
def execute_sequence_task(self, execution_id):
    """Execute a sequence step-by-step."""
    from apps.integrations.models import ActionExecution, ExecutionStatus
    from apps.integrations.services import IntegrationService

    try:
        execution = ActionExecution.objects.select_related("tenant", "sequence").get(id=execution_id)
    except ActionExecution.DoesNotExist:
        logger.error("execution_not_found", execution_id=execution_id)
        return

    if execution.status in (ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED):
        logger.info("execution_skipped", execution_id=execution_id, status=execution.status)
        return

    try:
        IntegrationService.run_sequence(execution)
        logger.info(
            "sequence_executed",
            execution_id=execution_id,
            sequence=execution.sequence.slug if execution.sequence else "?",
            status=execution.status,
        )
    except Exception as exc:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = str(exc)
        execution.save(update_fields=["status", "error_message"])
        logger.error("sequence_execution_failed", execution_id=execution_id, error=str(exc))


@shared_task(bind=True, max_retries=1)
def test_jira_connection_task(self, connection_id):
    """Test a Jira connection asynchronously."""
    from apps.integrations.models import JiraConnection
    from apps.integrations.services import IntegrationService

    try:
        connection = JiraConnection.objects.get(id=connection_id)
    except JiraConnection.DoesNotExist:
        logger.error("connection_not_found", connection_id=connection_id)
        return {"success": False, "message": "Connection nicht gefunden."}

    success, message = IntegrationService.test_connection(connection)
    logger.info("jira_connection_tested", connection_id=connection_id, success=success, message=message)
    return {"success": success, "message": message}


@shared_task(bind=True, max_retries=0)
def check_all_jira_connections(self):
    """Daily health check: test all active Jira connections.

    If a connection fails, notify the tenant owner via email.
    Registered as a Celery Beat periodic task in apps.py.
    """
    from apps.integrations.models import JiraConnection
    from apps.integrations.services import IntegrationService
    from apps.users.models import Membership

    connections = JiraConnection.objects.filter(is_active=True).select_related("tenant")
    tested = 0
    failed = 0

    for connection in connections:
        was_healthy = connection.last_test_success is not False  # True or None = "was OK"
        success, message = IntegrationService.test_connection(connection)
        tested += 1

        if not success:
            failed += 1
            logger.warning(
                "jira_connection_health_check_failed",
                tenant=connection.tenant.name,
                connection_id=str(connection.id),
                message=message,
            )

            # Nur benachrichtigen wenn der Status sich verschlechtert hat
            # (war vorher OK oder noch nie getestet → jetzt kaputt)
            if was_healthy:
                _notify_owner_connection_failed(connection, message)

    logger.info(
        "jira_health_check_complete",
        tested=tested,
        failed=failed,
    )
    return {"tested": tested, "failed": failed}


def _notify_owner_connection_failed(connection, error_message):
    """Send an email to the tenant owner about a broken Jira connection.

    Uses the tenant's configured email provider. If no provider is configured,
    the notification is skipped (logged only) — we never fall back to Django's
    global email backend.
    """
    from apps.emails.models import EmailProviderConnection as EmailConn
    from apps.emails.provider_service import EmailProviderService
    from apps.users.models import Membership

    owner_membership = Membership.objects.filter(
        tenant=connection.tenant,
        role="owner",
        is_active=True,
    ).select_related("user").first()

    if not owner_membership:
        logger.warning("no_owner_for_tenant", tenant=connection.tenant.name)
        return

    tenant_name = connection.tenant.name

    # Check if tenant has an active email provider
    if not EmailConn.objects.filter(tenant=connection.tenant, is_active=True).exists():
        logger.warning(
            "jira_health_notification_skipped_no_email_provider",
            tenant=tenant_name,
        )
        return

    backend, from_email = EmailProviderService.get_backend_for_tenant(connection.tenant)
    if backend is None:
        logger.warning(
            "jira_health_notification_skipped_no_email_provider",
            tenant=tenant_name,
        )
        return

    owner_email = owner_membership.user.email
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

    try:
        msg = EmailMultiAlternatives(
            subject=f"Jira-Verbindung fehlgeschlagen — {tenant_name}",
            body=(
                f"Hallo,\n\n"
                f"der tägliche Verbindungstest für die Jira-Integration "
                f"von \"{tenant_name}\" ist fehlgeschlagen.\n\n"
                f"Fehlermeldung: {error_message}\n\n"
                f"Das bedeutet wahrscheinlich, dass dein Jira API-Token "
                f"abgelaufen oder ungültig ist. Jira-Aktionen (z.B. Projekt- "
                f"oder Ticket-Erstellung) funktionieren nicht, bis der Token "
                f"erneuert wird.\n\n"
                f"So behebst du das Problem:\n"
                f"1. Erstelle einen neuen API-Token unter: "
                f"https://id.atlassian.com/manage-profile/security/api-tokens\n"
                f"2. Gehe zu {frontend_url}/integrationen/jira/verbindung\n"
                f"3. Gib den neuen Token ein und speichere\n"
                f"4. Klicke auf \"Verbindung testen\"\n\n"
                f"Viele Grüße,\n"
                f"Dein Aftersales-System"
            ),
            from_email=from_email,
            to=[owner_email],
            connection=backend,
        )
        msg.send()
        logger.info(
            "jira_connection_failure_email_sent",
            tenant=tenant_name,
            recipient=owner_email,
        )
    except Exception as e:
        logger.error(
            "jira_connection_failure_email_error",
            tenant=tenant_name,
            error=str(e),
        )
