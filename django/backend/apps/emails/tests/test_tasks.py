import pytest
from unittest.mock import patch, MagicMock

from apps.emails.models import (
    EmailLog,
    EmailStatus,
    EnrollmentStatus,
    SequenceEnrollment,
)
from apps.emails.tasks import send_email_task, check_sequence_completion


@pytest.mark.django_db
class TestSendEmailTask:
    def test_sends_email_and_updates_status(self, tenant, system_template):
        from apps.emails.services import EmailService

        with patch("apps.emails.tasks.send_email_task") as mock_dispatch:
            mock_dispatch.apply_async.return_value.id = "celery-task-id"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        assert log.status == EmailStatus.PENDING

        # Now actually run the task (with mocked email sending + provider)
        mock_backend = MagicMock()
        with (
            patch("apps.emails.tasks.EmailProviderService.get_backend_for_tenant", return_value=(mock_backend, "noreply@example.com")),
            patch("apps.emails.tasks.EmailMultiAlternatives") as mock_email_cls,
        ):
            mock_msg = MagicMock()
            mock_email_cls.return_value = mock_msg

            send_email_task(str(log.id))

        mock_msg.attach_alternative.assert_called_once()
        mock_msg.send.assert_called_once()

        log.refresh_from_db()
        assert log.status == EmailStatus.SENT
        assert log.sent_at is not None

    def test_fails_without_provider(self, tenant, system_template):
        """No active email provider → EmailLog gets FAILED with clear message."""
        from apps.emails.services import EmailService

        with patch("apps.emails.tasks.send_email_task") as mock_dispatch:
            mock_dispatch.apply_async.return_value.id = "celery-no-provider"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        # No provider configured → get_backend_for_tenant returns (None, None)
        send_email_task(str(log.id))

        log.refresh_from_db()
        assert log.status == EmailStatus.FAILED
        assert "Kein E-Mail-Provider konfiguriert" in log.error_message

    def test_skips_already_sent(self, tenant, system_template):
        from apps.emails.services import EmailService

        with patch("apps.emails.tasks.send_email_task") as mock_dispatch:
            mock_dispatch.apply_async.return_value.id = "celery-skip"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        log.status = EmailStatus.SENT
        log.save(update_fields=["status"])

        with patch("apps.emails.tasks.EmailMultiAlternatives") as mock_email_cls:
            send_email_task(str(log.id))
            mock_email_cls.assert_not_called()

    def test_skips_cancelled(self, tenant, system_template):
        from apps.emails.services import EmailService

        with patch("apps.emails.tasks.send_email_task") as mock_dispatch:
            mock_dispatch.apply_async.return_value.id = "celery-cancelled"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        log.status = EmailStatus.CANCELLED
        log.save(update_fields=["status"])

        with patch("apps.emails.tasks.EmailMultiAlternatives") as mock_email_cls:
            send_email_task(str(log.id))
            mock_email_cls.assert_not_called()

    def test_cancels_if_enrollment_cancelled(self, tenant, system_sequence):
        from apps.emails.services import EmailService

        with patch("apps.emails.tasks.send_email_task") as mock_dispatch:
            mock_dispatch.apply_async.return_value.id = "celery-enroll"
            enrollment = EmailService.start_sequence(
                tenant=tenant,
                sequence_slug="test-sequence",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        # Cancel enrollment
        enrollment.status = EnrollmentStatus.CANCELLED
        enrollment.save(update_fields=["status"])

        log = EmailLog.objects.filter(sequence_enrollment=enrollment).first()

        with patch("apps.emails.tasks.EmailMultiAlternatives") as mock_email_cls:
            send_email_task(str(log.id))
            mock_email_cls.assert_not_called()

        log.refresh_from_db()
        assert log.status == EmailStatus.CANCELLED

    def test_handles_nonexistent_log(self):
        import uuid
        # Should not raise, just log error
        send_email_task(str(uuid.uuid4()))


@pytest.mark.django_db
class TestCheckSequenceCompletion:
    def test_marks_completed_when_all_sent(self, tenant, system_sequence):
        from apps.emails.services import EmailService

        with patch("apps.emails.tasks.send_email_task") as mock_dispatch:
            mock_dispatch.apply_async.return_value.id = "celery-comp"
            enrollment = EmailService.start_sequence(
                tenant=tenant,
                sequence_slug="test-sequence",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        # Mark all logs as sent
        EmailLog.objects.filter(sequence_enrollment=enrollment).update(
            status=EmailStatus.SENT,
        )

        check_sequence_completion(str(enrollment.id))

        enrollment.refresh_from_db()
        assert enrollment.status == EnrollmentStatus.COMPLETED
        assert enrollment.completed_at is not None

    def test_does_not_complete_with_pending_emails(self, tenant, multi_step_sequence):
        from apps.emails.services import EmailService

        with patch("apps.emails.tasks.send_email_task") as mock_dispatch:
            mock_dispatch.apply_async.return_value.id = "celery-pend"
            enrollment = EmailService.start_sequence(
                tenant=tenant,
                sequence_slug="multi-step-sequence",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max"},
            )

        # Only mark one of two as sent
        first_log = EmailLog.objects.filter(sequence_enrollment=enrollment).first()
        first_log.status = EmailStatus.SENT
        first_log.save(update_fields=["status"])

        check_sequence_completion(str(enrollment.id))

        enrollment.refresh_from_db()
        assert enrollment.status == EnrollmentStatus.ACTIVE
