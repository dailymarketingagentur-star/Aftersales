"""Task-related business logic, extracted for reuse by views and Celery tasks."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.utils import timezone

from apps.clients.models import Client
from apps.tasks.models import ClientActivity, Subtask, Task, TaskList, TaskListItem, TaskTemplate

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from apps.tenants.models import Tenant
    from apps.users.models import User

logger = logging.getLogger(__name__)


class TaskService:
    """Stateless service for task generation and recurring-schedule helpers."""

    # ------------------------------------------------------------------
    # Core: generate tasks for a single client from a task list
    # ------------------------------------------------------------------
    @staticmethod
    def generate_tasks_for_client(
        *,
        tenant: Tenant,
        client: Client,
        task_list: TaskList,
        reference_date: date | None = None,
        author: User | None = None,
    ) -> list[Task]:
        """
        Generate concrete Task instances for *client* from *task_list*.

        Parameters
        ----------
        tenant : Tenant
        client : Client
        task_list : TaskList
        reference_date : date | None
            Base date used together with each template's day_offset to compute
            ``due_date``.  Defaults to ``client.start_date`` (original behaviour).
            Recurring schedules pass ``date.today()``.
        author : User | None
            User who triggered the generation.  ``None`` when called from Celery.
        """
        if reference_date is None:
            reference_date = client.start_date

        # Collect item metadata (group_label, day_offset overrides)
        items = task_list.items.order_by("group_position", "position")
        template_ids = list(items.values_list("task_template_id", flat=True))
        item_meta: dict[str, dict] = {}
        for item in items:
            item_meta[str(item.task_template_id)] = {
                "group_label": item.group_label,
                "day_offset": item.day_offset,
            }

        # Fetch templates (system + tenant)
        qs = TaskTemplate.objects.filter(
            Q(tenant=tenant) | Q(tenant__isnull=True),
            is_active=True,
        )
        if template_ids:
            qs = qs.filter(id__in=template_ids)

        created_tasks: list[Task] = []
        for tpl in qs:
            # Duplicate check: only open/in-progress tasks block re-generation
            if Task.objects.filter(
                client=client,
                template=tpl,
            ).exclude(
                status__in=["completed", "skipped"],
            ).exists():
                continue

            # day_offset: item override > template default
            meta = item_meta.get(str(tpl.pk), {})
            effective_day_offset = meta.get("day_offset")
            if effective_day_offset is None:
                effective_day_offset = tpl.day_offset

            due_date = None
            if reference_date and effective_day_offset is not None:
                due_date = reference_date + timedelta(days=effective_day_offset)

            # Tasks with future due_date start as "planned", others as "open"
            today = date.today()
            initial_status = Task.Status.PLANNED if (due_date and due_date > today) else Task.Status.OPEN

            task = Task.objects.create(
                tenant=tenant,
                client=client,
                template=tpl,
                title=tpl.name,
                description=tpl.description,
                action_type=tpl.action_type,
                phase=tpl.phase,
                priority=tpl.priority,
                status=initial_status,
                due_date=due_date,
                email_template=tpl.email_template,
                action_template=tpl.action_template,
                action_sequence=tpl.action_sequence,
                email_sequence=tpl.email_sequence,
                group_label=meta.get("group_label", ""),
                source_list=task_list,
            )

            # M2M: email templates
            if tpl.email_templates.exists():
                task.email_templates.set(tpl.email_templates.all())

            # Subtasks from template
            for i, title in enumerate(tpl.default_subtasks):
                Subtask.objects.create(
                    tenant=tenant, task=task, title=title, position=i,
                )

            created_tasks.append(task)

        # Timeline entry
        if created_tasks:
            ClientActivity.objects.create(
                tenant=tenant,
                client=client,
                activity_type=ClientActivity.ActivityType.TASK_CREATED,
                content=f"{len(created_tasks)} Aufgaben aus Vorlagen generiert.",
                author=author,
            )

        return created_tasks

    # ------------------------------------------------------------------
    # Helpers for recurring schedules
    # ------------------------------------------------------------------
    @staticmethod
    def get_eligible_clients(schedule) -> QuerySet[Client]:
        """
        Return the Client queryset matching the schedule's ``client_scope``.
        Only active/onboarding clients are included.
        """
        base = Client.objects.filter(
            tenant=schedule.tenant,
            status__in=[Client.Status.ACTIVE, Client.Status.ONBOARDING],
        )

        if schedule.client_scope == "all_active":
            return base

        if schedule.client_scope == "by_service_type":
            service_type_ids = schedule.service_types.values_list("id", flat=True)
            return base.filter(services__service_type_id__in=service_type_ids).distinct()

        if schedule.client_scope == "explicit":
            return base.filter(id__in=schedule.clients.values_list("id", flat=True))

        return Client.objects.none()

    @staticmethod
    def compute_next_run(frequency: str, from_dt=None):
        """
        Compute the next execution datetime based on *frequency*.

        ``from_dt`` defaults to ``timezone.now()``.  The result is always at
        08:00 on the computed day.
        """
        if from_dt is None:
            from_dt = timezone.now()

        base_date = from_dt.date()

        if frequency == "weekly":
            next_date = base_date + timedelta(weeks=1)
        elif frequency == "biweekly":
            next_date = base_date + timedelta(weeks=2)
        elif frequency == "monthly":
            next_date = base_date + relativedelta(months=1)
        elif frequency == "quarterly":
            next_date = base_date + relativedelta(months=3)
        else:
            next_date = base_date + timedelta(weeks=1)

        return timezone.make_aware(
            timezone.datetime(next_date.year, next_date.month, next_date.day, 8, 0),
        )

    # ------------------------------------------------------------------
    # Execute a task's integration action (email, jira, webhook, etc.)
    # ------------------------------------------------------------------
    @staticmethod
    def execute_task_action(
        *,
        task: Task,
        tenant: Tenant,
        user: User | None = None,
    ) -> dict:
        """
        Execute the integration action linked to *task*.

        Returns ``{"success": bool, "detail": str, "execution_id": str|None}``.
        Used by both manual views and the auto-trigger Celery task.
        """
        from apps.emails.models import EmailProviderConnection
        from apps.emails.services import EmailService
        from apps.integrations.services import IntegrationService

        client = task.client
        action_type = task.action_type

        context = {
            "FIRST_NAME": client.contact_first_name or (client.name.split()[0] if client.name else ""),
            "LAST_NAME": client.contact_last_name or "",
            "CLIENT_NAME": client.name,
            "KUNDENNAME": client.name,
            "FIRMENNAME": client.name,
            "TENANT_NAME": tenant.name if tenant else "",
        }

        # --- Email ---
        if action_type == "email":
            if not EmailProviderConnection.objects.filter(tenant=tenant, is_active=True).exists():
                return {"success": False, "detail": "Kein E-Mail-Provider konfiguriert.", "execution_id": None}

            recipient_email = client.contact_email
            if not recipient_email:
                return {"success": False, "detail": "Mandant hat keine E-Mail-Adresse.", "execution_id": None}

            # Determine template slug: first email_template from M2M
            email_tpls = list(task.email_templates.all()[:1])
            if not email_tpls:
                return {"success": False, "detail": "Keine E-Mail-Vorlage verknuepft.", "execution_id": None}
            template_slug = email_tpls[0].slug

            # NPS special case
            if template_slug == "nps-review":
                try:
                    from apps.nps.services import NPSService
                    NPSService.send_survey(tenant=tenant, client=client, task=task)
                except Exception as e:
                    return {"success": False, "detail": f"NPS-Umfrage fehlgeschlagen: {e}", "execution_id": None}

                ClientActivity.objects.create(
                    tenant=tenant, client=client, task=task,
                    activity_type=ClientActivity.ActivityType.NPS_SENT,
                    content=f"NPS-Umfrage an {recipient_email} gesendet (Auto-Trigger).",
                    author=user,
                )
                return {"success": True, "detail": "NPS-Umfrage gesendet.", "execution_id": None}

            try:
                EmailService.send(
                    tenant=tenant,
                    template_slug=template_slug,
                    recipient_email=recipient_email,
                    context=context,
                )
            except Exception as e:
                return {"success": False, "detail": f"E-Mail fehlgeschlagen: {e}", "execution_id": None}

            ClientActivity.objects.create(
                tenant=tenant, client=client, task=task,
                activity_type=ClientActivity.ActivityType.EMAIL_SENT,
                content=f'E-Mail "{template_slug}" an {recipient_email} gesendet (Auto-Trigger).',
                author=user,
            )
            return {"success": True, "detail": "E-Mail gesendet.", "execution_id": None}

        # --- Email Sequence ---
        if action_type == "email_sequence":
            if not EmailProviderConnection.objects.filter(tenant=tenant, is_active=True).exists():
                return {"success": False, "detail": "Kein E-Mail-Provider konfiguriert.", "execution_id": None}

            if not task.email_sequence:
                return {"success": False, "detail": "Keine E-Mail-Sequenz verknuepft.", "execution_id": None}

            recipient_email = client.contact_email
            if not recipient_email:
                return {"success": False, "detail": "Mandant hat keine E-Mail-Adresse.", "execution_id": None}

            try:
                enrollment = EmailService.start_sequence(
                    tenant=tenant,
                    sequence_slug=task.email_sequence.slug,
                    recipient_email=recipient_email,
                    context=context,
                )
            except Exception as e:
                return {"success": False, "detail": f"E-Mail-Sequenz fehlgeschlagen: {e}", "execution_id": None}

            ClientActivity.objects.create(
                tenant=tenant, client=client, task=task,
                activity_type=ClientActivity.ActivityType.EMAIL_SENT,
                content=f'E-Mail-Sequenz "{task.email_sequence.name}" gestartet (Auto-Trigger).',
                author=user,
            )
            return {"success": True, "detail": "E-Mail-Sequenz gestartet.", "execution_id": str(enrollment.pk)}

        # --- Jira ---
        if action_type in ("jira_project", "jira_ticket"):
            try:
                if task.action_sequence:
                    execution = IntegrationService.start_sequence(
                        tenant=tenant,
                        sequence_slug=task.action_sequence.slug,
                        context=context,
                        user=user,
                        entity_type="client",
                        entity_id=str(client.pk),
                    )
                elif task.action_template:
                    execution = IntegrationService.execute(
                        tenant=tenant,
                        template_slug=task.action_template.slug,
                        context=context,
                        user=user,
                        entity_type="client",
                        entity_id=str(client.pk),
                    )
                else:
                    return {"success": False, "detail": "Keine Jira-Aktion verknuepft.", "execution_id": None}
            except Exception as e:
                return {"success": False, "detail": f"Jira-Aktion fehlgeschlagen: {e}", "execution_id": None}

            action_name = (
                task.action_sequence.name if task.action_sequence
                else task.action_template.name if task.action_template
                else "Unbekannt"
            )
            ClientActivity.objects.create(
                tenant=tenant, client=client, task=task,
                activity_type=ClientActivity.ActivityType.JIRA_EXECUTED,
                content=f'Jira-Aktion "{action_name}" gestartet (Auto-Trigger).',
                author=user,
            )
            return {"success": True, "detail": "Jira-Aktion gestartet.", "execution_id": str(execution.pk)}

        # --- Webhook ---
        if action_type == "webhook":
            try:
                if task.action_sequence:
                    execution = IntegrationService.start_sequence(
                        tenant=tenant,
                        sequence_slug=task.action_sequence.slug,
                        context=context,
                        user=user,
                        entity_type="client",
                        entity_id=str(client.pk),
                    )
                elif task.action_template:
                    execution = IntegrationService.execute(
                        tenant=tenant,
                        template_slug=task.action_template.slug,
                        context=context,
                        user=user,
                        entity_type="client",
                        entity_id=str(client.pk),
                    )
                else:
                    return {"success": False, "detail": "Keine Webhook-Aktion verknuepft.", "execution_id": None}
            except Exception as e:
                return {"success": False, "detail": f"Webhook fehlgeschlagen: {e}", "execution_id": None}

            action_name = (
                task.action_sequence.name if task.action_sequence
                else task.action_template.name if task.action_template
                else "Unbekannt"
            )
            ClientActivity.objects.create(
                tenant=tenant, client=client, task=task,
                activity_type=ClientActivity.ActivityType.WEBHOOK_EXECUTED,
                content=f'Webhook "{action_name}" gestartet (Auto-Trigger).',
                author=user,
            )
            return {"success": True, "detail": "Webhook gestartet.", "execution_id": str(execution.pk)}

        # --- WhatsApp ---
        if action_type == "whatsapp":
            from apps.clients.models import ClientPhoneNumber
            from apps.integrations.models import WhatsAppConnection

            conn = WhatsAppConnection.objects.filter(tenant=tenant, is_active=True).first()
            if not conn:
                return {"success": False, "detail": "Keine WhatsApp-Verbindung konfiguriert.", "execution_id": None}

            # Get client phone number
            phone = ClientPhoneNumber.objects.filter(client=client).first()
            if not phone:
                return {"success": False, "detail": "Mandant hat keine Telefonnummer.", "execution_id": None}

            body_text = context.get("WHATSAPP_TEXT", f"Hallo {context.get('FIRST_NAME', client.name)}, hier ist eine Nachricht von {context.get('TENANT_NAME', '')}.")

            try:
                import requests as http_requests
                from apps.emails.models import WhatsAppMessage, WhatsAppMessageDirection, WhatsAppMessageStatus

                to_number = phone.number.lstrip("+")
                token = conn.get_access_token()
                resp = http_requests.post(
                    f"https://graph.facebook.com/v21.0/{conn.phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": to_number,
                        "type": "text",
                        "text": {"body": body_text},
                    },
                    timeout=15,
                )

                if resp.status_code not in (200, 201):
                    error_data = resp.json().get("error", {})
                    return {"success": False, "detail": f"WhatsApp API Fehler: {error_data.get('message', resp.status_code)}", "execution_id": None}

                resp_data = resp.json()
                wa_message_id = None
                messages = resp_data.get("messages", [])
                if messages:
                    wa_message_id = messages[0].get("id")

                WhatsAppMessage.objects.create(
                    tenant=tenant,
                    wa_message_id=wa_message_id,
                    direction=WhatsAppMessageDirection.OUTBOUND,
                    from_number=conn.display_phone_number,
                    to_number=phone.number,
                    body_text=body_text,
                    status=WhatsAppMessageStatus.SENT,
                    client=client,
                    metadata=resp_data,
                )
            except Exception as e:
                return {"success": False, "detail": f"WhatsApp fehlgeschlagen: {e}", "execution_id": None}

            ClientActivity.objects.create(
                tenant=tenant, client=client, task=task,
                activity_type=ClientActivity.ActivityType.WHATSAPP_SENT,
                content=f"WhatsApp an {phone.number} gesendet (Auto-Trigger).",
                author=user,
            )
            return {"success": True, "detail": "WhatsApp-Nachricht gesendet.", "execution_id": None}

        # --- Health Check / Churn Check (require manual form submission) ---
        if action_type in ("health_check", "churn_check"):
            return {"success": False, "detail": "Erfordert manuelle Eingabe.", "execution_id": None}

        return {"success": False, "detail": f"Unbekannter action_type: {action_type}", "execution_id": None}

    # ------------------------------------------------------------------
    # Remove a loaded task list from a client
    # ------------------------------------------------------------------
    @staticmethod
    def remove_list_from_client(
        *,
        tenant: Tenant,
        client: Client,
        task_list: TaskList,
        author: User | None = None,
    ) -> dict:
        """
        Delete all open/in_progress tasks with source_list=task_list for this client.
        Completed/skipped tasks are preserved for history.

        Returns ``{"deleted_count": int, "list_name": str}``.
        """
        qs = Task.objects.filter(
            tenant=tenant,
            client=client,
            source_list=task_list,
            status__in=[Task.Status.PLANNED, Task.Status.OPEN, Task.Status.IN_PROGRESS],
        )
        deleted_count = qs.count()
        qs.delete()

        ClientActivity.objects.create(
            tenant=tenant,
            client=client,
            activity_type=ClientActivity.ActivityType.LIST_REMOVED,
            content=f'Aufgabenliste "{task_list.name}" entfernt ({deleted_count} offene Aufgaben gelöscht).',
            author=author,
        )

        return {"deleted_count": deleted_count, "list_name": task_list.name}
