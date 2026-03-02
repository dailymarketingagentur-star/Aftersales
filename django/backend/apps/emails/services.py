import hashlib
from datetime import timedelta

import structlog
from django.db import transaction
from django.utils import timezone

logger = structlog.get_logger()


class EmailService:
    """Central email service. Other apps call send() or start_sequence() — nothing else needed."""

    @staticmethod
    @transaction.atomic
    def send(tenant, template_slug, recipient_email, context, idempotency_key=None, scheduled_at=None):
        """Send a single email (immediately or scheduled).

        Returns the EmailLog instance. If an identical idempotency_key
        already exists, the existing log is returned without re-sending.
        """
        from apps.emails.models import EmailLog, EmailStatus
        from apps.emails.tasks import send_email_task

        template = EmailService._resolve_template(tenant, template_slug)
        rendered_subject = EmailService._render(template.subject, context)
        rendered_body = EmailService._render(template.body_html, context)

        if idempotency_key is None:
            idempotency_key = EmailService._generate_idempotency_key(
                tenant_id=str(tenant.id),
                template_slug=template_slug,
                recipient_email=recipient_email,
                context=context,
            )

        existing = EmailLog.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            logger.info(
                "email_deduplicated",
                idempotency_key=idempotency_key,
                email_log_id=str(existing.id),
            )
            return existing

        email_log = EmailLog.objects.create(
            tenant=tenant,
            template=template,
            template_slug=template_slug,
            recipient_email=recipient_email,
            subject=rendered_subject,
            body_html=rendered_body,
            status=EmailStatus.PENDING,
            context=context,
            scheduled_at=scheduled_at,
            idempotency_key=idempotency_key,
        )

        task = send_email_task.apply_async(
            args=[str(email_log.id)],
            eta=scheduled_at,
        )
        email_log.celery_task_id = task.id
        email_log.save(update_fields=["celery_task_id"])

        logger.info(
            "email_dispatched",
            email_log_id=str(email_log.id),
            template_slug=template_slug,
            recipient=recipient_email,
            scheduled_at=str(scheduled_at) if scheduled_at else "immediate",
        )
        return email_log

    @staticmethod
    @transaction.atomic
    def start_sequence(tenant, sequence_slug, recipient_email, context):
        """Enroll a recipient in an email sequence.

        Returns the SequenceEnrollment. If already enrolled, returns
        the existing enrollment without creating duplicates.
        """
        from apps.emails.models import EnrollmentStatus, SequenceEnrollment

        sequence = EmailService._resolve_sequence(tenant, sequence_slug)

        existing = SequenceEnrollment.objects.filter(
            tenant=tenant,
            sequence=sequence,
            recipient_email=recipient_email,
        ).first()
        if existing:
            logger.info(
                "sequence_enrollment_exists",
                enrollment_id=str(existing.id),
                sequence_slug=sequence_slug,
                recipient=recipient_email,
            )
            return existing

        enrollment = SequenceEnrollment.objects.create(
            tenant=tenant,
            sequence=sequence,
            recipient_email=recipient_email,
            context=context,
            status=EnrollmentStatus.ACTIVE,
        )

        now = timezone.now()
        steps = sequence.steps.filter(is_active=True).order_by("position")
        for step in steps:
            scheduled_at = now + timedelta(seconds=step.total_delay_seconds)
            idempotency_key = f"seq-{enrollment.id}-step-{step.position}"

            EmailService.send(
                tenant=tenant,
                template_slug=step.template.slug,
                recipient_email=recipient_email,
                context=context,
                idempotency_key=idempotency_key,
                scheduled_at=scheduled_at if step.total_delay_seconds > 0 else None,
            )

            # Link the created log to the enrollment
            from apps.emails.models import EmailLog

            EmailLog.objects.filter(idempotency_key=idempotency_key).update(
                sequence_enrollment=enrollment,
            )

        logger.info(
            "sequence_started",
            enrollment_id=str(enrollment.id),
            sequence_slug=sequence_slug,
            recipient=recipient_email,
            step_count=steps.count(),
        )
        return enrollment

    @staticmethod
    @transaction.atomic
    def cancel_sequence(enrollment_id):
        """Cancel a sequence enrollment and all its pending emails."""
        from apps.emails.models import EmailStatus, EnrollmentStatus, SequenceEnrollment

        enrollment = SequenceEnrollment.objects.select_for_update().get(id=enrollment_id)
        enrollment.status = EnrollmentStatus.CANCELLED
        enrollment.save(update_fields=["status"])

        cancelled_count = enrollment.email_logs.filter(
            status=EmailStatus.PENDING,
        ).update(status=EmailStatus.CANCELLED)

        logger.info(
            "sequence_cancelled",
            enrollment_id=str(enrollment.id),
            cancelled_emails=cancelled_count,
        )
        return enrollment

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_template(tenant, slug):
        """Resolve template: tenant-specific first, then system default (tenant=NULL)."""
        from apps.emails.models import EmailTemplate

        template = EmailTemplate.objects.filter(
            tenant=tenant, slug=slug, is_active=True,
        ).first()
        if template:
            return template

        template = EmailTemplate.objects.filter(
            tenant__isnull=True, slug=slug, is_active=True,
        ).first()
        if template:
            return template

        raise EmailTemplate.DoesNotExist(
            f"No active email template found for slug '{slug}' "
            f"(tenant={tenant.id if tenant else 'system'})."
        )

    @staticmethod
    def _resolve_sequence(tenant, slug):
        """Resolve sequence: tenant-specific first, then system default."""
        from apps.emails.models import EmailSequence

        sequence = EmailSequence.objects.filter(
            tenant=tenant, slug=slug, is_active=True,
        ).first()
        if sequence:
            return sequence

        sequence = EmailSequence.objects.filter(
            tenant__isnull=True, slug=slug, is_active=True,
        ).first()
        if sequence:
            return sequence

        raise EmailSequence.DoesNotExist(
            f"No active email sequence found for slug '{slug}' "
            f"(tenant={tenant.id if tenant else 'system'})."
        )

    @staticmethod
    def _render(template_text, context):
        """Render {{PLACEHOLDER}} variables. Simple str.replace — no Django template engine."""
        result = template_text
        for key, value in context.items():
            result = result.replace("{{" + key + "}}", str(value))
        return result

    @staticmethod
    def _generate_idempotency_key(tenant_id, template_slug, recipient_email, context):
        """Generate a SHA256 idempotency key as fallback."""
        raw = f"{tenant_id}:{template_slug}:{recipient_email}:{sorted(context.items())}"
        return hashlib.sha256(raw.encode()).hexdigest()
