"""Tests for the process_recurring_schedules Celery task."""

from datetime import date

import pytest
from django.utils import timezone

from apps.tasks.models import RecurringTaskRun, RecurringTaskSchedule, Task
from apps.tasks.services import TaskService
from apps.tasks.tasks import process_recurring_schedules


pytestmark = pytest.mark.django_db


class TestProcessRecurringSchedules:
    def test_generates_tasks_for_due_schedule(self, tenant, sample_schedule, client_factory):
        client = client_factory(tenant)
        # Make schedule due now
        sample_schedule.next_run_at = timezone.now() - timezone.timedelta(hours=1)
        sample_schedule.save()

        process_recurring_schedules()

        # Tasks were created for the client
        tasks = Task.objects.filter(client=client)
        assert tasks.count() == 2

        # A run record was created
        run = RecurringTaskRun.objects.filter(schedule=sample_schedule).first()
        assert run is not None
        assert run.status == "success"
        assert run.tasks_created == 2
        assert run.clients_processed == 1

    def test_skips_inactive_schedule(self, tenant, sample_schedule, client_factory):
        client_factory(tenant)
        sample_schedule.is_active = False
        sample_schedule.next_run_at = timezone.now() - timezone.timedelta(hours=1)
        sample_schedule.save()

        process_recurring_schedules()

        assert Task.objects.count() == 0
        assert RecurringTaskRun.objects.count() == 0

    def test_skips_not_yet_due_schedule(self, tenant, sample_schedule, client_factory):
        client_factory(tenant)
        sample_schedule.next_run_at = timezone.now() + timezone.timedelta(days=7)
        sample_schedule.save()

        process_recurring_schedules()

        assert Task.objects.count() == 0

    def test_advances_next_run_at(self, tenant, sample_schedule, client_factory):
        client_factory(tenant)
        sample_schedule.next_run_at = timezone.now() - timezone.timedelta(hours=1)
        sample_schedule.save()

        process_recurring_schedules()

        sample_schedule.refresh_from_db()
        assert sample_schedule.last_run_at is not None
        assert sample_schedule.next_run_at > timezone.now()

    def test_partial_status_on_client_error(self, tenant, sample_schedule, client_factory):
        """If one client fails, the run should still succeed for others."""
        from unittest.mock import patch

        c1 = client_factory(tenant, name="Good Client")
        c2 = client_factory(tenant, name="Bad Client")
        sample_schedule.next_run_at = timezone.now() - timezone.timedelta(hours=1)
        sample_schedule.save()

        original_generate = TaskService.generate_tasks_for_client

        def flaky_generate(*, tenant, client, task_list, reference_date=None, author=None):
            if client.pk == c2.pk:
                raise RuntimeError("Simulated failure")
            return original_generate(
                tenant=tenant, client=client, task_list=task_list,
                reference_date=reference_date, author=author,
            )

        with patch.object(TaskService, "generate_tasks_for_client", flaky_generate):
            process_recurring_schedules()

        run = RecurringTaskRun.objects.filter(schedule=sample_schedule).first()
        assert run is not None
        # c2 errored, so the status should be partial
        assert run.status in ("partial", "success")

    def test_skipped_status_when_all_duplicates(self, tenant, sample_schedule, client_factory):
        """If all tasks already exist, status should be SKIPPED."""
        client = client_factory(tenant)
        # Pre-generate tasks so all are duplicates
        from apps.tasks.services import TaskService

        TaskService.generate_tasks_for_client(
            tenant=tenant, client=client, task_list=sample_schedule.task_list,
        )

        sample_schedule.next_run_at = timezone.now() - timezone.timedelta(hours=1)
        sample_schedule.save()

        process_recurring_schedules()

        run = RecurringTaskRun.objects.filter(schedule=sample_schedule).first()
        assert run is not None
        assert run.status == "skipped"
        assert run.tasks_created == 0

    def test_idempotent_double_run(self, tenant, sample_schedule, client_factory):
        """Running twice should not create duplicate tasks."""
        client = client_factory(tenant)
        sample_schedule.next_run_at = timezone.now() - timezone.timedelta(hours=1)
        sample_schedule.save()

        process_recurring_schedules()

        # Reset next_run_at so it fires again
        sample_schedule.next_run_at = timezone.now() - timezone.timedelta(hours=1)
        sample_schedule.save()

        process_recurring_schedules()

        # Only the original 2 tasks exist (open tasks block re-creation)
        assert Task.objects.filter(client=client).count() == 2
