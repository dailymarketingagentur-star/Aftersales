"""Celery tasks for the tasks app."""

import logging
from datetime import date

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Daily promotion: planned → open when due_date arrives
# ---------------------------------------------------------------------------
@shared_task
def promote_planned_tasks():
    """
    Daily beat task (06:55): set all tasks with status=planned and
    due_date <= today to status=open so they become actionable.
    """
    from apps.tasks.models import Task

    today = date.today()
    updated = Task.objects.filter(
        status=Task.Status.PLANNED,
        due_date__lte=today,
    ).update(status=Task.Status.OPEN)

    logger.info("promote_planned_tasks: %d tasks promoted to open", updated)


# Action types that can be auto-triggered
AUTO_TRIGGERABLE_TYPES = {"email", "email_sequence", "jira_project", "jira_ticket", "webhook"}


@shared_task(bind=True, max_retries=1)
def process_recurring_schedules(self):
    """
    Daily beat task: find all due RecurringTaskSchedules and generate tasks.

    Each schedule is processed independently.  Per-client errors are caught
    so that one failing client does not block the others.
    """
    from apps.tasks.models import RecurringTaskRun, RecurringTaskSchedule
    from apps.tasks.services import TaskService

    now = timezone.now()
    due_schedules = RecurringTaskSchedule.objects.filter(
        is_active=True,
        next_run_at__lte=now,
    ).select_related("task_list", "tenant")

    for schedule in due_schedules:
        _execute_schedule(schedule, now, TaskService)


def _execute_schedule(schedule, now, task_service_cls):
    """Process a single schedule: generate tasks for all eligible clients."""
    from apps.tasks.models import RecurringTaskRun
    from apps.tasks.services import TaskService

    run = RecurringTaskRun.objects.create(
        tenant=schedule.tenant,
        schedule=schedule,
        status=RecurringTaskRun.Status.SUCCESS,
        started_at=now,
    )

    clients = TaskService.get_eligible_clients(schedule)
    total_created = 0
    total_skipped = 0
    errors: list[str] = []
    details: dict[str, dict] = {}

    for client in clients.iterator():
        try:
            created = TaskService.generate_tasks_for_client(
                tenant=schedule.tenant,
                client=client,
                task_list=schedule.task_list,
                reference_date=date.today(),
                author=None,
            )
            count = len(created)
            total_created += count
            details[str(client.id)] = {
                "name": client.name,
                "tasks_created": count,
            }
        except Exception as exc:
            logger.exception("Recurring schedule %s failed for client %s", schedule.id, client.id)
            errors.append(f"{client.name}: {exc}")
            total_skipped += 1
            details[str(client.id)] = {
                "name": client.name,
                "error": str(exc),
            }

    # Determine final status
    clients_processed = clients.count()
    if errors and total_created == 0:
        run_status = RecurringTaskRun.Status.FAILED
    elif errors:
        run_status = RecurringTaskRun.Status.PARTIAL
    elif total_created == 0 and clients_processed > 0:
        run_status = RecurringTaskRun.Status.SKIPPED
    else:
        run_status = RecurringTaskRun.Status.SUCCESS

    run.status = run_status
    run.completed_at = timezone.now()
    run.clients_processed = clients_processed
    run.tasks_created = total_created
    run.tasks_skipped = total_skipped
    run.error_message = "\n".join(errors)
    run.details = details
    run.save()

    # Advance schedule regardless of outcome (no endless retries)
    schedule.last_run_at = now
    schedule.next_run_at = TaskService.compute_next_run(schedule.frequency, now)
    schedule.save(update_fields=["last_run_at", "next_run_at", "updated_at"])

    logger.info(
        "Schedule %s done: %d clients, %d tasks created, %d skipped",
        schedule.id,
        clients_processed,
        total_created,
        total_skipped,
    )


# ---------------------------------------------------------------------------
# Auto-trigger: execute a single task action
# ---------------------------------------------------------------------------
@shared_task(bind=True, max_retries=3)
def auto_trigger_task_action(self, task_id):
    """Execute the integration action for a single task (auto-trigger)."""
    from apps.tasks.models import ClientActivity, Task
    from apps.tasks.services import TaskService

    try:
        task = Task.objects.select_related(
            "client", "template", "action_template", "action_sequence", "email_sequence",
        ).prefetch_related("email_templates").get(pk=task_id)
    except Task.DoesNotExist:
        logger.warning("auto_trigger: Task %s not found", task_id)
        return

    # Guards
    if task.status not in (Task.Status.OPEN, Task.Status.IN_PROGRESS):
        logger.info("auto_trigger: Task %s already %s — skipping", task_id, task.status)
        return

    if task.action_type not in AUTO_TRIGGERABLE_TYPES:
        logger.info("auto_trigger: Task %s has action_type=%s — not auto-triggerable", task_id, task.action_type)
        return

    tenant = task.tenant
    now = timezone.now()
    task.auto_trigger_attempted_at = now
    task.save(update_fields=["auto_trigger_attempted_at", "updated_at"])

    result = TaskService.execute_task_action(task=task, tenant=tenant, user=None)

    if result["success"]:
        task.status = Task.Status.COMPLETED
        task.completed_at = now
        task.auto_trigger_error = ""
        task.save(update_fields=["status", "completed_at", "auto_trigger_error", "updated_at"])

        ClientActivity.objects.create(
            tenant=tenant,
            client=task.client,
            task=task,
            activity_type=ClientActivity.ActivityType.AUTO_TRIGGER_SUCCESS,
            content=f'Auto-Trigger: "{task.title}" erfolgreich ausgeführt.',
        )
        logger.info("auto_trigger: Task %s completed successfully", task_id)
    else:
        task.auto_trigger_error = result["detail"]
        task.save(update_fields=["auto_trigger_error", "updated_at"])

        ClientActivity.objects.create(
            tenant=tenant,
            client=task.client,
            task=task,
            activity_type=ClientActivity.ActivityType.AUTO_TRIGGER_FAILED,
            content=f'Auto-Trigger: "{task.title}" fehlgeschlagen — {result["detail"]}',
        )
        logger.warning("auto_trigger: Task %s failed — %s", task_id, result["detail"])

        # Retry with exponential backoff (60s, 180s, 540s)
        raise self.retry(countdown=60 * (3 ** self.request.retries), exc=Exception(result["detail"]))


# ---------------------------------------------------------------------------
# Periodic task: find and dispatch auto-trigger tasks
# ---------------------------------------------------------------------------
@shared_task
def process_auto_trigger_tasks():
    """
    Every 15 min: find tasks that are due, have auto_on_due trigger mode,
    and dispatch individual auto_trigger_task_action tasks.
    """
    from apps.tasks.models import Task, TriggerMode

    today = date.today()

    # Tasks where trigger_mode is explicitly auto_on_due
    explicit = Q(trigger_mode=TriggerMode.AUTO_ON_DUE)
    # Tasks where trigger_mode is NULL and template has auto_on_due
    inherited = Q(trigger_mode__isnull=True, template__trigger_mode=TriggerMode.AUTO_ON_DUE)

    tasks = Task.objects.filter(
        (explicit | inherited),
        status__in=[Task.Status.OPEN, Task.Status.IN_PROGRESS],
        due_date__lte=today,
        action_type__in=AUTO_TRIGGERABLE_TYPES,
    ).values_list("id", flat=True)

    count = 0
    for task_id in tasks:
        auto_trigger_task_action.delay(str(task_id))
        count += 1

    logger.info("process_auto_trigger_tasks: dispatched %d tasks", count)
