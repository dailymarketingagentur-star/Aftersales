from datetime import date

import pytest

from apps.clients.models import Client, Service, ServiceType
from apps.tasks.models import RecurringTaskSchedule, TaskList, TaskListItem, TaskTemplate
from apps.users.models import Membership


@pytest.fixture
def admin_membership(user, tenant):
    """Make the default user an admin of the default tenant."""
    return Membership.objects.create(user=user, tenant=tenant, role="admin")


@pytest.fixture
def task_template_factory(db):
    """Factory to create TaskTemplates."""

    def create(tenant=None, name=None, **kwargs):
        count = TaskTemplate.objects.count() + 1
        if name is None:
            name = f"Template {count}"
        defaults = {
            "action_type": "manual",
            "phase": 1,
            "day_offset": 0,
            "priority": "medium",
            "is_active": True,
        }
        defaults.update(kwargs)
        return TaskTemplate.objects.create(tenant=tenant, name=name, **defaults)

    return create


@pytest.fixture
def task_list_factory(db):
    """Factory to create TaskLists."""

    def create(tenant=None, name=None, **kwargs):
        count = TaskList.objects.count() + 1
        if name is None:
            name = f"Task List {count}"
        return TaskList.objects.create(tenant=tenant, name=name, **kwargs)

    return create


@pytest.fixture
def client_factory(db):
    """Factory to create Clients."""

    def create(tenant, name=None, status="active", **kwargs):
        count = Client.objects.filter(tenant=tenant).count() + 1
        if name is None:
            name = f"Test Client {count}"
        if "start_date" not in kwargs:
            kwargs["start_date"] = date.today()
        return Client.objects.create(tenant=tenant, name=name, status=status, **kwargs)

    return create


@pytest.fixture
def service_type_factory(db):
    """Factory to create ServiceTypes."""

    def create(tenant, name="SEO", **kwargs):
        return ServiceType.objects.create(tenant=tenant, name=name, **kwargs)

    return create


@pytest.fixture
def sample_task_list(tenant, task_template_factory, task_list_factory):
    """A TaskList with 2 templates linked via TaskListItems."""
    tpl1 = task_template_factory(tenant=tenant, name="Monthly Report", day_offset=0)
    tpl2 = task_template_factory(tenant=tenant, name="Review Call", day_offset=3, default_subtasks=["Prepare", "Execute"])
    task_list = task_list_factory(tenant=tenant, name="Monthly Workflow")
    TaskListItem.objects.create(task_list=task_list, task_template=tpl1, position=0)
    TaskListItem.objects.create(task_list=task_list, task_template=tpl2, position=1)
    return task_list


@pytest.fixture
def sample_schedule(tenant, sample_task_list):
    """A RecurringTaskSchedule for the sample_task_list."""
    from django.utils import timezone

    from apps.tasks.services import TaskService

    return RecurringTaskSchedule.objects.create(
        tenant=tenant,
        task_list=sample_task_list,
        frequency="monthly",
        is_active=True,
        client_scope="all_active",
        next_run_at=TaskService.compute_next_run("monthly"),
    )
