import structlog
from celery import shared_task
from django.utils import timezone

logger = structlog.get_logger()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_nps_followup(self, response_id):
    """Process follow-up actions based on NPS segment.

    - Promoter (9-10): Send promoter follow-up email + create testimonial task
    - Passive (7-8): Send passive follow-up email
    - Detractor (0-6): Send detractor follow-up email + create escalation task
    """
    from apps.emails.services import EmailService
    from apps.nps.models import NPSResponse, TestimonialRequest
    from apps.tasks.models import ClientActivity, Task, TaskTemplate

    try:
        response = NPSResponse.objects.select_related("survey", "client", "tenant").get(id=response_id)
    except NPSResponse.DoesNotExist:
        logger.warning("nps_followup_response_not_found", response_id=response_id)
        return

    tenant = response.tenant
    client = response.client

    context = {
        "FIRST_NAME": client.contact_first_name or client.name.split()[0] if client.name else "",
        "LAST_NAME": client.contact_last_name or "",
        "CLIENT_NAME": client.name,
        "KUNDENNAME": client.name,
        "FIRMENNAME": client.name,
        "TENANT_NAME": tenant.name,
        "NPS_SCORE": str(response.score),
    }

    # Send segment-specific follow-up email
    template_map = {
        NPSResponse.Segment.PROMOTER: "nps-followup-promoter",
        NPSResponse.Segment.PASSIVE: "nps-followup-passive",
        NPSResponse.Segment.DETRACTOR: "nps-followup-detractor",
    }
    template_slug = template_map.get(response.segment)

    if template_slug and client.contact_email:
        try:
            EmailService.send(
                tenant=tenant,
                template_slug=template_slug,
                recipient_email=client.contact_email,
                context=context,
                idempotency_key=f"nps-followup-{response.id}",
            )
        except Exception:
            logger.exception("nps_followup_email_failed", response_id=response_id, segment=response.segment)

    # Segment-specific actions
    if response.segment == NPSResponse.Segment.PROMOTER:
        # Create testimonial request
        TestimonialRequest.objects.create(
            tenant=tenant,
            client=client,
            nps_response=response,
            request_type=TestimonialRequest.RequestType.WRITTEN,
        )

        # Create testimonial task if template exists
        tpl = TaskTemplate.objects.filter(slug="testimonial-anfrage", is_active=True).first()
        if tpl:
            Task.objects.create(
                tenant=tenant,
                client=client,
                template=tpl,
                title=tpl.name,
                description=tpl.description,
                action_type=tpl.action_type,
                priority=tpl.priority,
                phase=tpl.phase,
                due_date=timezone.now().date() + timezone.timedelta(days=5),
            )

    elif response.segment == NPSResponse.Segment.DETRACTOR:
        # Create urgent escalation task
        Task.objects.create(
            tenant=tenant,
            client=client,
            title=f"NPS Eskalation: {client.name} (Score {response.score})",
            description=(
                f"Mandant {client.name} hat einen NPS-Score von {response.score} gegeben.\n"
                f"Kommentar: {response.comment or '(kein Kommentar)'}\n\n"
                "Bitte sofort Kontakt aufnehmen und Probleme klaeren."
            ),
            action_type="manual",
            priority="critical",
            due_date=timezone.now().date() + timezone.timedelta(days=1),
        )

    # Create activity entry
    ClientActivity.objects.create(
        tenant=tenant,
        client=client,
        activity_type=ClientActivity.ActivityType.NPS_RECEIVED,
        content=f"NPS-Score {response.score} ({response.get_segment_display()}) erhalten."
        + (f" Kommentar: {response.comment}" if response.comment else ""),
    )

    logger.info(
        "nps_followup_processed",
        response_id=response_id,
        segment=response.segment,
        client=client.name,
    )


@shared_task
def process_nps_campaigns():
    """Daily check: send surveys for active campaigns based on trigger rules.

    - day_offset: Clients whose start_date + day_offset = today
    - quarterly: Clients due for quarterly survey
    """
    from apps.clients.models import Client
    from apps.nps.models import NPSCampaign, NPSSurvey
    from apps.nps.services import NPSService
    from apps.tenants.models import Tenant

    today = timezone.now().date()
    campaigns = NPSCampaign.objects.filter(is_active=True).select_related("tenant")

    total_sent = 0

    for campaign in campaigns:
        tenant = campaign.tenant

        if campaign.trigger_type == NPSCampaign.TriggerType.DAY_OFFSET:
            # Find clients whose start_date + day_offset = today
            target_start_date = today - timezone.timedelta(days=campaign.day_offset)
            clients = Client.objects.filter(
                tenant=tenant,
                start_date=target_start_date,
                status="active",
            )

            for client in clients:
                if not client.contact_email:
                    continue
                # Skip if survey already exists (pending or responded)
                if NPSSurvey.objects.filter(
                    tenant=tenant,
                    client=client,
                    campaign=campaign,
                    status__in=[NPSSurvey.Status.PENDING, NPSSurvey.Status.RESPONDED],
                ).exists():
                    continue

                try:
                    NPSService.send_survey(tenant=tenant, client=client, campaign=campaign)
                    total_sent += 1
                except Exception:
                    logger.exception(
                        "nps_campaign_send_failed",
                        campaign_id=str(campaign.id),
                        client=client.name,
                    )

        elif campaign.trigger_type == NPSCampaign.TriggerType.QUARTERLY:
            # Find active clients with no pending survey from this campaign
            clients = Client.objects.filter(tenant=tenant, status="active")
            for client in clients:
                if not client.contact_email:
                    continue
                # Check if client already has a recent survey (within repeat interval)
                recent = NPSSurvey.objects.filter(
                    tenant=tenant,
                    client=client,
                    campaign=campaign,
                    created_at__gte=timezone.now() - timezone.timedelta(days=max(campaign.repeat_interval_days, 90)),
                ).exists()
                if recent:
                    continue

                try:
                    NPSService.send_survey(tenant=tenant, client=client, campaign=campaign)
                    total_sent += 1
                except Exception:
                    logger.exception(
                        "nps_campaign_send_failed",
                        campaign_id=str(campaign.id),
                        client=client.name,
                    )

    logger.info("nps_campaigns_processed", total_sent=total_sent)
