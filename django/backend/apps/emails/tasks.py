import re
from urllib.parse import quote

import structlog
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from apps.emails.provider_service import EmailProviderService

logger = structlog.get_logger()

BACKOFF_SCHEDULE = [60, 120, 240]


@shared_task(bind=True, max_retries=3)
def send_email_task(self, email_log_id):
    """Send a single email. This is the ONLY place in the system that calls .send()."""
    from apps.emails.models import EmailLog, EmailStatus, EnrollmentStatus

    try:
        email_log = EmailLog.objects.select_related(
            "tenant", "sequence_enrollment",
        ).get(id=email_log_id)
    except EmailLog.DoesNotExist:
        logger.error("email_log_not_found", email_log_id=email_log_id)
        return

    # Skip if already sent or cancelled
    if email_log.status in (EmailStatus.SENT, EmailStatus.CANCELLED):
        logger.info(
            "email_skipped",
            email_log_id=email_log_id,
            status=email_log.status,
        )
        return

    # Cancel if enrollment was aborted
    if (
        email_log.sequence_enrollment
        and email_log.sequence_enrollment.status == EnrollmentStatus.CANCELLED
    ):
        email_log.status = EmailStatus.CANCELLED
        email_log.save(update_fields=["status"])
        logger.info("email_cancelled_by_enrollment", email_log_id=email_log_id)
        return

    try:
        # Build tracking URLs
        base_url = getattr(settings, "BACKEND_URL", "")
        tracking_pixel_url = f"{base_url}/api/v1/emails/track/{email_log.tracking_id}/open/"
        tracking_pixel = f'<img src="{tracking_pixel_url}" width="1" height="1" alt="" style="display:none;" />'

        # Rewrite links for click tracking
        body_with_tracking = _rewrite_links_for_tracking(
            email_log.body_html,
            email_log.tracking_id,
            base_url,
        )

        # Render full HTML via base_layout.html
        html_content = render_to_string("emails/base_layout.html", {
            "subject": email_log.subject,
            "body_html": body_with_tracking,
            "tracking_pixel": tracking_pixel,
            "tenant": email_log.tenant,
        })

        # Resolve per-tenant email backend — kein Fallback auf Django global
        backend, tenant_from_email = EmailProviderService.get_backend_for_tenant(email_log.tenant)

        if backend is None:
            email_log.status = EmailStatus.FAILED
            email_log.error_message = (
                "Kein E-Mail-Provider konfiguriert. "
                "Bitte richte SMTP oder SendGrid unter Integrationen → E-Mail ein."
            )
            email_log.save(update_fields=["status", "error_message"])
            logger.warning(
                "email_no_provider",
                email_log_id=email_log_id,
                tenant=str(email_log.tenant.id),
            )
            return  # Kein Retry — fehlender Provider ist kein transientes Problem

        # Build and send
        msg = EmailMultiAlternatives(
            subject=email_log.subject,
            body=email_log.subject,  # plain-text fallback
            from_email=tenant_from_email,
            to=[email_log.recipient_email],
            connection=backend,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        email_log.status = EmailStatus.SENT
        email_log.sent_at = timezone.now()
        email_log.save(update_fields=["status", "sent_at"])

        logger.info(
            "email_sent",
            email_log_id=email_log_id,
            recipient=email_log.recipient_email,
            template_slug=email_log.template_slug,
        )

        # Check if sequence is complete
        if email_log.sequence_enrollment:
            check_sequence_completion.delay(str(email_log.sequence_enrollment.id))

    except Exception as exc:
        countdown = BACKOFF_SCHEDULE[self.request.retries] if self.request.retries < len(BACKOFF_SCHEDULE) else BACKOFF_SCHEDULE[-1]
        logger.error(
            "email_send_failed",
            email_log_id=email_log_id,
            error=str(exc),
            retry=self.request.retries,
        )

        if self.request.retries >= self.max_retries:
            email_log.status = EmailStatus.FAILED
            email_log.error_message = str(exc)
            email_log.save(update_fields=["status", "error_message"])
            return

        email_log.error_message = str(exc)
        email_log.save(update_fields=["error_message"])
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=1)
def check_sequence_completion(self, enrollment_id):
    """Check if all steps of a sequence enrollment have been sent."""
    from apps.emails.models import EmailStatus, EnrollmentStatus, SequenceEnrollment

    try:
        enrollment = SequenceEnrollment.objects.select_related("sequence").get(
            id=enrollment_id,
        )
    except SequenceEnrollment.DoesNotExist:
        logger.error("enrollment_not_found", enrollment_id=enrollment_id)
        return

    if enrollment.status != EnrollmentStatus.ACTIVE:
        return

    total_steps = enrollment.sequence.steps.filter(is_active=True).count()
    sent_count = enrollment.email_logs.filter(status=EmailStatus.SENT).count()

    if sent_count >= total_steps:
        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.completed_at = timezone.now()
        enrollment.current_step = total_steps
        enrollment.save(update_fields=["status", "completed_at", "current_step"])
        logger.info(
            "sequence_completed",
            enrollment_id=enrollment_id,
            sent=sent_count,
            total=total_steps,
        )
    else:
        enrollment.current_step = sent_count
        enrollment.save(update_fields=["current_step"])


def _rewrite_links_for_tracking(html, tracking_id, base_url):
    """Rewrite <a href="..."> links for click tracking."""

    def replace_link(match):
        original_url = match.group(1)
        # Don't track mailto:, tel:, or anchor links
        if original_url.startswith(("mailto:", "tel:", "#", "{{", "{%")):
            return match.group(0)
        tracking_url = f"{base_url}/api/v1/emails/track/{tracking_id}/click/?url={quote(original_url)}"
        return match.group(0).replace(original_url, tracking_url)

    return re.sub(r'<a\s[^>]*href="([^"]*)"', replace_link, html)
