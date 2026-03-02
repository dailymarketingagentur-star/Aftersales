import pytest
from unittest.mock import patch

from apps.emails.models import (
    EmailLog,
    EmailStatus,
    EnrollmentStatus,
    SequenceEnrollment,
)
from apps.emails.services import EmailService


@pytest.mark.django_db
class TestEmailServiceSend:
    def test_send_creates_log_and_dispatches_task(self, tenant, system_template):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-123"

            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        assert log.status == EmailStatus.PENDING
        assert log.recipient_email == "kunde@example.com"
        assert log.subject == "Hallo Max!"
        assert "Willkommen, Max bei Agentur" in log.body_html
        assert log.template == system_template
        assert log.template_slug == "test-template"
        mock_task.apply_async.assert_called_once()

    def test_send_uses_tenant_override(self, tenant, system_template, tenant_template):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-456"

            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        assert log.template == tenant_template
        assert log.subject == "Hey Max — Custom!"

    def test_send_idempotency_prevents_duplicate(self, tenant, system_template):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-789"

            log1 = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
                idempotency_key="unique-key-1",
            )
            log2 = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
                idempotency_key="unique-key-1",
            )

        assert log1.id == log2.id
        assert mock_task.apply_async.call_count == 1

    def test_send_raises_for_missing_template(self, tenant):
        with pytest.raises(Exception, match="No active email template"):
            EmailService.send(
                tenant=tenant,
                template_slug="nonexistent",
                recipient_email="test@example.com",
                context={},
            )

    def test_send_with_scheduled_at(self, tenant, system_template):
        from django.utils import timezone
        from datetime import timedelta

        future = timezone.now() + timedelta(hours=1)

        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-sched"

            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
                scheduled_at=future,
            )

        assert log.scheduled_at == future
        call_kwargs = mock_task.apply_async.call_args
        assert call_kwargs.kwargs.get("eta") == future or call_kwargs[1].get("eta") == future


@pytest.mark.django_db
class TestEmailServiceSequence:
    def test_start_sequence_creates_enrollment_and_emails(self, tenant, system_sequence):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-seq"

            enrollment = EmailService.start_sequence(
                tenant=tenant,
                sequence_slug="test-sequence",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        assert enrollment.status == EnrollmentStatus.ACTIVE
        assert enrollment.recipient_email == "kunde@example.com"
        assert EmailLog.objects.filter(sequence_enrollment=enrollment).count() == 1

    def test_start_sequence_multi_step(self, tenant, multi_step_sequence):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-multi"

            enrollment = EmailService.start_sequence(
                tenant=tenant,
                sequence_slug="multi-step-sequence",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max"},
            )

        assert EmailLog.objects.filter(sequence_enrollment=enrollment).count() == 2

    def test_start_sequence_deduplicates_enrollment(self, tenant, system_sequence):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-dedup"

            e1 = EmailService.start_sequence(
                tenant=tenant,
                sequence_slug="test-sequence",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )
            e2 = EmailService.start_sequence(
                tenant=tenant,
                sequence_slug="test-sequence",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        assert e1.id == e2.id

    def test_cancel_sequence(self, tenant, system_sequence):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-cancel"

            enrollment = EmailService.start_sequence(
                tenant=tenant,
                sequence_slug="test-sequence",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        cancelled = EmailService.cancel_sequence(enrollment.id)
        assert cancelled.status == EnrollmentStatus.CANCELLED

        # Pending emails should be cancelled too
        assert EmailLog.objects.filter(
            sequence_enrollment=enrollment,
            status=EmailStatus.CANCELLED,
        ).count() == 1


@pytest.mark.django_db
class TestEmailServiceRender:
    def test_render_replaces_placeholders(self):
        result = EmailService._render(
            "Hallo {{NAME}}, willkommen bei {{COMPANY}}!",
            {"NAME": "Max", "COMPANY": "Agentur"},
        )
        assert result == "Hallo Max, willkommen bei Agentur!"

    def test_render_leaves_unknown_placeholders(self):
        result = EmailService._render(
            "Hallo {{NAME}}, Ihr Code: {{CODE}}",
            {"NAME": "Max"},
        )
        assert "{{CODE}}" in result
