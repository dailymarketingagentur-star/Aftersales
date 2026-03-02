"""Tests for TaskService (generate_tasks_for_client, eligible clients, compute_next_run)."""

from datetime import date, timedelta

import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from apps.clients.models import Client, Service
from apps.tasks.models import ClientActivity, Subtask, Task
from apps.tasks.services import TaskService


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# generate_tasks_for_client
# ---------------------------------------------------------------------------
class TestGenerateTasksForClient:
    def test_creates_tasks_from_list(self, tenant, sample_task_list, client_factory):
        client = client_factory(tenant)
        tasks = TaskService.generate_tasks_for_client(
            tenant=tenant,
            client=client,
            task_list=sample_task_list,
        )
        assert len(tasks) == 2
        assert tasks[0].title == "Monthly Report"
        assert tasks[1].title == "Review Call"

    def test_creates_subtasks_from_template(self, tenant, sample_task_list, client_factory):
        client = client_factory(tenant)
        tasks = TaskService.generate_tasks_for_client(
            tenant=tenant,
            client=client,
            task_list=sample_task_list,
        )
        review_task = next(t for t in tasks if t.title == "Review Call")
        subtasks = list(Subtask.objects.filter(task=review_task).order_by("position"))
        assert len(subtasks) == 2
        assert subtasks[0].title == "Prepare"
        assert subtasks[1].title == "Execute"

    def test_due_date_uses_reference_date(self, tenant, sample_task_list, client_factory):
        """When reference_date is given, due_date = reference_date + day_offset."""
        client = client_factory(tenant)
        ref = date(2026, 6, 1)
        tasks = TaskService.generate_tasks_for_client(
            tenant=tenant,
            client=client,
            task_list=sample_task_list,
            reference_date=ref,
        )
        report = next(t for t in tasks if t.title == "Monthly Report")
        review = next(t for t in tasks if t.title == "Review Call")
        assert report.due_date == date(2026, 6, 1)  # offset=0
        assert review.due_date == date(2026, 6, 4)  # offset=3

    def test_due_date_uses_client_start_date_by_default(self, tenant, sample_task_list, client_factory):
        client = client_factory(tenant, start_date=date(2026, 1, 15))
        tasks = TaskService.generate_tasks_for_client(
            tenant=tenant,
            client=client,
            task_list=sample_task_list,
        )
        report = next(t for t in tasks if t.title == "Monthly Report")
        assert report.due_date == date(2026, 1, 15)

    def test_duplicate_check_skips_open_tasks(self, tenant, sample_task_list, client_factory):
        client = client_factory(tenant)
        # First generation
        TaskService.generate_tasks_for_client(
            tenant=tenant, client=client, task_list=sample_task_list,
        )
        # Second generation — should create nothing (open tasks block)
        tasks = TaskService.generate_tasks_for_client(
            tenant=tenant, client=client, task_list=sample_task_list,
        )
        assert len(tasks) == 0

    def test_completed_tasks_allow_regeneration(self, tenant, sample_task_list, client_factory):
        client = client_factory(tenant)
        TaskService.generate_tasks_for_client(
            tenant=tenant, client=client, task_list=sample_task_list,
        )
        # Mark all as completed
        Task.objects.filter(client=client).update(status="completed")
        # Now re-generation should work
        tasks = TaskService.generate_tasks_for_client(
            tenant=tenant, client=client, task_list=sample_task_list,
        )
        assert len(tasks) == 2

    def test_creates_client_activity(self, tenant, sample_task_list, client_factory, user):
        client = client_factory(tenant)
        TaskService.generate_tasks_for_client(
            tenant=tenant, client=client, task_list=sample_task_list, author=user,
        )
        activity = ClientActivity.objects.filter(client=client).first()
        assert activity is not None
        assert activity.activity_type == "task_created"
        assert "2 Aufgaben" in activity.content
        assert activity.author == user

    def test_no_activity_when_nothing_created(self, tenant, sample_task_list, client_factory):
        client = client_factory(tenant)
        TaskService.generate_tasks_for_client(
            tenant=tenant, client=client, task_list=sample_task_list,
        )
        # Second call — nothing created
        count_before = ClientActivity.objects.filter(client=client).count()
        TaskService.generate_tasks_for_client(
            tenant=tenant, client=client, task_list=sample_task_list,
        )
        assert ClientActivity.objects.filter(client=client).count() == count_before


# ---------------------------------------------------------------------------
# get_eligible_clients
# ---------------------------------------------------------------------------
class TestGetEligibleClients:
    def test_all_active_scope(self, tenant, sample_schedule, client_factory):
        c1 = client_factory(tenant, status="active")
        c2 = client_factory(tenant, status="onboarding")
        c3 = client_factory(tenant, status="churned")
        sample_schedule.client_scope = "all_active"
        clients = TaskService.get_eligible_clients(sample_schedule)
        client_ids = set(clients.values_list("id", flat=True))
        assert c1.id in client_ids
        assert c2.id in client_ids
        assert c3.id not in client_ids

    def test_by_service_type_scope(self, tenant, sample_schedule, client_factory, service_type_factory):
        seo = service_type_factory(tenant, name="SEO")
        sea = service_type_factory(tenant, name="SEA")
        c1 = client_factory(tenant)
        c2 = client_factory(tenant)
        # c1 has SEO service, c2 has SEA
        Service.objects.create(tenant=tenant, client=c1, service_type=seo, name="SEO Basic")
        Service.objects.create(tenant=tenant, client=c2, service_type=sea, name="SEA Basic")

        sample_schedule.client_scope = "by_service_type"
        sample_schedule.save()
        sample_schedule.service_types.set([seo])

        clients = TaskService.get_eligible_clients(sample_schedule)
        client_ids = set(clients.values_list("id", flat=True))
        assert c1.id in client_ids
        assert c2.id not in client_ids

    def test_explicit_scope(self, tenant, sample_schedule, client_factory):
        c1 = client_factory(tenant)
        c2 = client_factory(tenant)

        sample_schedule.client_scope = "explicit"
        sample_schedule.save()
        sample_schedule.clients.set([c1])

        clients = TaskService.get_eligible_clients(sample_schedule)
        client_ids = set(clients.values_list("id", flat=True))
        assert c1.id in client_ids
        assert c2.id not in client_ids

    def test_explicit_scope_excludes_churned(self, tenant, sample_schedule, client_factory):
        c1 = client_factory(tenant, status="churned")
        sample_schedule.client_scope = "explicit"
        sample_schedule.save()
        sample_schedule.clients.set([c1])
        clients = TaskService.get_eligible_clients(sample_schedule)
        assert clients.count() == 0


# ---------------------------------------------------------------------------
# compute_next_run
# ---------------------------------------------------------------------------
class TestComputeNextRun:
    def test_weekly(self):
        now = timezone.now()
        result = TaskService.compute_next_run("weekly", now)
        assert result.date() == now.date() + timedelta(weeks=1)
        assert result.hour == 8
        assert result.minute == 0

    def test_biweekly(self):
        now = timezone.now()
        result = TaskService.compute_next_run("biweekly", now)
        assert result.date() == now.date() + timedelta(weeks=2)

    def test_monthly(self):
        now = timezone.make_aware(timezone.datetime(2026, 1, 31, 10, 0))
        result = TaskService.compute_next_run("monthly", now)
        assert result.date() == date(2026, 2, 28)  # dateutil handles month-end

    def test_quarterly(self):
        now = timezone.make_aware(timezone.datetime(2026, 3, 1, 10, 0))
        result = TaskService.compute_next_run("quarterly", now)
        assert result.date() == date(2026, 6, 1)

    def test_defaults_to_now_when_no_from_dt(self):
        result = TaskService.compute_next_run("weekly")
        assert result.date() == date.today() + timedelta(weeks=1)
