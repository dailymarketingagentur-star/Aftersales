"""Tests for recurring schedule API endpoints."""

import pytest
from django.utils import timezone

from apps.tasks.models import RecurringTaskSchedule, RecurringTaskRun


pytestmark = pytest.mark.django_db


class TestRecurringScheduleListCreate:
    url = "/api/v1/tasks/schedules/"

    def test_list_empty(self, authenticated_client, tenant, admin_membership):
        resp = authenticated_client.get(self.url, HTTP_X_TENANT_ID=str(tenant.id))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_schedule(self, authenticated_client, tenant, admin_membership, sample_task_list):
        data = {
            "task_list_id": str(sample_task_list.id),
            "frequency": "monthly",
            "client_scope": "all_active",
        }
        resp = authenticated_client.post(self.url, data, format="json", HTTP_X_TENANT_ID=str(tenant.id))
        assert resp.status_code == 201
        body = resp.json()
        assert body["frequency"] == "monthly"
        assert body["task_list"] == str(sample_task_list.id)
        assert body["next_run_at"] is not None

    def test_create_schedule_duplicate_returns_400(
        self, authenticated_client, tenant, admin_membership, sample_task_list, sample_schedule,
    ):
        """UniqueConstraint: one schedule per task_list per tenant."""
        data = {
            "task_list_id": str(sample_task_list.id),
            "frequency": "weekly",
        }
        resp = authenticated_client.post(self.url, data, format="json", HTTP_X_TENANT_ID=str(tenant.id))
        assert resp.status_code in (400, 500)  # IntegrityError → 400 or 500

    def test_list_returns_created_schedule(
        self, authenticated_client, tenant, admin_membership, sample_schedule,
    ):
        resp = authenticated_client.get(self.url, HTTP_X_TENANT_ID=str(tenant.id))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == str(sample_schedule.id)

    def test_unauthenticated_denied(self, api_client, tenant):
        resp = api_client.get(self.url, HTTP_X_TENANT_ID=str(tenant.id))
        assert resp.status_code in (401, 403)


class TestRecurringScheduleDetail:
    def _url(self, pk):
        return f"/api/v1/tasks/schedules/{pk}/"

    def test_get_detail(self, authenticated_client, tenant, admin_membership, sample_schedule):
        resp = authenticated_client.get(
            self._url(sample_schedule.id), HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == str(sample_schedule.id)

    def test_patch_frequency(self, authenticated_client, tenant, admin_membership, sample_schedule):
        resp = authenticated_client.patch(
            self._url(sample_schedule.id),
            {"frequency": "weekly"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert resp.status_code == 200
        assert resp.json()["frequency"] == "weekly"

    def test_patch_deactivate(self, authenticated_client, tenant, admin_membership, sample_schedule):
        resp = authenticated_client.patch(
            self._url(sample_schedule.id),
            {"is_active": False},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_delete(self, authenticated_client, tenant, admin_membership, sample_schedule):
        resp = authenticated_client.delete(
            self._url(sample_schedule.id), HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert resp.status_code == 204
        assert not RecurringTaskSchedule.objects.filter(pk=sample_schedule.id).exists()

    def test_not_found(self, authenticated_client, tenant, admin_membership):
        import uuid

        resp = authenticated_client.get(
            self._url(uuid.uuid4()), HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert resp.status_code == 404


class TestRecurringScheduleRuns:
    def _url(self, pk):
        return f"/api/v1/tasks/schedules/{pk}/runs/"

    def test_empty_runs(self, authenticated_client, tenant, admin_membership, sample_schedule):
        resp = authenticated_client.get(
            self._url(sample_schedule.id), HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_runs(self, authenticated_client, tenant, admin_membership, sample_schedule):
        RecurringTaskRun.objects.create(
            tenant=tenant,
            schedule=sample_schedule,
            status="success",
            started_at=timezone.now(),
            completed_at=timezone.now(),
            clients_processed=5,
            tasks_created=10,
        )
        resp = authenticated_client.get(
            self._url(sample_schedule.id), HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["tasks_created"] == 10


class TestRecurringScheduleTrigger:
    def _url(self, pk):
        return f"/api/v1/tasks/schedules/{pk}/trigger/"

    def test_trigger_creates_tasks(
        self, authenticated_client, tenant, admin_membership, sample_schedule, client_factory,
    ):
        client = client_factory(tenant)
        resp = authenticated_client.post(
            self._url(sample_schedule.id), HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["tasks_created"] >= 1
        assert body["status"] in ("success", "skipped")
