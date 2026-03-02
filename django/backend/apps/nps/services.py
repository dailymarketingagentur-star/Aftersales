import uuid
from datetime import date, timedelta

import structlog
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.emails.services import EmailService

logger = structlog.get_logger()


class NPSService:
    """Central NPS service — other apps call send_survey() and submit_response()."""

    @staticmethod
    @transaction.atomic
    def send_survey(*, tenant, client, campaign=None, task=None):
        """Create an NPSSurvey with token and send the NPS email.

        Returns the NPSSurvey instance.
        """
        from apps.nps.models import NPSSurvey

        survey = NPSSurvey.objects.create(
            tenant=tenant,
            client=client,
            campaign=campaign,
            task=task,
            token=uuid.uuid4(),
            status=NPSSurvey.Status.PENDING,
            sent_at=timezone.now(),
        )

        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        survey_url = f"{frontend_url}/survey/{survey.token}"

        context = {
            "NPS_URL": survey_url,
            "FIRST_NAME": client.contact_first_name or client.name.split()[0] if client.name else "",
            "LAST_NAME": client.contact_last_name or "",
            "CLIENT_NAME": client.name,
            "KUNDENNAME": client.name,
            "FIRMENNAME": client.name,
            "TENANT_NAME": tenant.name if tenant else "",
        }

        template_slug = "nps-review"
        if campaign and campaign.email_template:
            template_slug = campaign.email_template.slug

        try:
            email_log = EmailService.send(
                tenant=tenant,
                template_slug=template_slug,
                recipient_email=client.contact_email,
                context=context,
                idempotency_key=f"nps-survey-{survey.id}",
            )
            survey.email_log = email_log
            survey.save(update_fields=["email_log"])
        except Exception:
            logger.exception("nps_email_send_failed", survey_id=str(survey.id))
            raise

        logger.info(
            "nps_survey_sent",
            survey_id=str(survey.id),
            client=client.name,
            token=str(survey.token),
        )
        return survey

    @staticmethod
    @transaction.atomic
    def submit_response(*, survey, score, comment="", ip_address=None, user_agent=""):
        """Submit an NPS response for a survey.

        Returns the NPSResponse instance.
        Raises ValueError if survey is expired or already responded.
        """
        from apps.nps.models import NPSResponse

        if survey.is_expired:
            raise ValueError("Diese Umfrage ist abgelaufen.")

        if survey.status == survey.Status.RESPONDED:
            raise ValueError("Diese Umfrage wurde bereits beantwortet.")

        response = NPSResponse.objects.create(
            tenant=survey.tenant,
            survey=survey,
            client=survey.client,
            score=score,
            comment=comment,
            ip_address=ip_address,
            user_agent=user_agent,
            responded_at=timezone.now(),
        )

        survey.status = survey.Status.RESPONDED
        survey.save(update_fields=["status", "updated_at"])

        # Auto-complete linked task
        if survey.task:
            from apps.tasks.models import Task

            task = survey.task
            if task.status not in (Task.Status.COMPLETED, Task.Status.SKIPPED):
                task.status = Task.Status.COMPLETED
                task.completed_at = timezone.now()
                task.save(update_fields=["status", "completed_at", "updated_at"])

        logger.info(
            "nps_response_submitted",
            response_id=str(response.id),
            score=score,
            segment=response.segment,
            client=survey.client.name,
        )
        return response

    @staticmethod
    def calculate_nps(tenant, date_from=None, date_to=None):
        """Calculate NPS score and segment distribution.

        Returns dict: {score, total, promoters, passives, detractors, promoter_pct, passive_pct, detractor_pct}
        """
        from apps.nps.models import NPSResponse

        qs = NPSResponse.objects.filter(tenant=tenant)
        if date_from:
            qs = qs.filter(responded_at__gte=date_from)
        if date_to:
            qs = qs.filter(responded_at__lte=date_to)

        total = qs.count()
        if total == 0:
            return {
                "score": 0,
                "total": 0,
                "promoters": 0,
                "passives": 0,
                "detractors": 0,
                "promoter_pct": 0,
                "passive_pct": 0,
                "detractor_pct": 0,
            }

        promoters = qs.filter(segment=NPSResponse.Segment.PROMOTER).count()
        passives = qs.filter(segment=NPSResponse.Segment.PASSIVE).count()
        detractors = qs.filter(segment=NPSResponse.Segment.DETRACTOR).count()

        promoter_pct = round(promoters / total * 100, 1)
        passive_pct = round(passives / total * 100, 1)
        detractor_pct = round(detractors / total * 100, 1)
        score = round(promoter_pct - detractor_pct)

        return {
            "score": score,
            "total": total,
            "promoters": promoters,
            "passives": passives,
            "detractors": detractors,
            "promoter_pct": promoter_pct,
            "passive_pct": passive_pct,
            "detractor_pct": detractor_pct,
        }

    @staticmethod
    def nps_over_time(tenant, months=12):
        """Monthly NPS values for trend chart.

        Returns list of dicts: [{month: "2026-01", score: 42, total: 5}, ...]
        """
        from apps.nps.models import NPSResponse

        cutoff = timezone.now() - timedelta(days=months * 30)
        qs = NPSResponse.objects.filter(
            tenant=tenant,
            responded_at__gte=cutoff,
        )

        monthly = (
            qs.annotate(month=TruncMonth("responded_at"))
            .values("month")
            .annotate(
                total=Count("id"),
                promoters=Count("id", filter=Q(segment=NPSResponse.Segment.PROMOTER)),
                detractors=Count("id", filter=Q(segment=NPSResponse.Segment.DETRACTOR)),
            )
            .order_by("month")
        )

        result = []
        for entry in monthly:
            total = entry["total"]
            if total > 0:
                score = round((entry["promoters"] / total - entry["detractors"] / total) * 100)
            else:
                score = 0
            result.append({
                "month": entry["month"].strftime("%Y-%m"),
                "score": score,
                "total": total,
            })

        return result

    @staticmethod
    def surveys_sent_count(tenant):
        """Total surveys sent for response rate calculation."""
        from apps.nps.models import NPSSurvey

        return NPSSurvey.objects.filter(tenant=tenant).count()

    @staticmethod
    def surveys_responded_count(tenant):
        """Total surveys responded."""
        from apps.nps.models import NPSSurvey

        return NPSSurvey.objects.filter(tenant=tenant, status=NPSSurvey.Status.RESPONDED).count()
