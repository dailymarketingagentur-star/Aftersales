from django.urls import path

from apps.tasks.views import (
    RecurringScheduleDetailView,
    RecurringScheduleListCreateView,
    RecurringScheduleRunsView,
    RecurringScheduleTriggerView,
    TaskDashboardView,
    TaskListDetailView,
    TaskListDuplicateView,
    TaskListListCreateView,
    TaskListReorderView,
    TaskListUsageView,
    TaskTemplateDetailView,
    TaskTemplateListCreateView,
)

app_name = "tasks"

urlpatterns = [
    path("dashboard/", TaskDashboardView.as_view(), name="task-dashboard"),
    path("templates/", TaskTemplateListCreateView.as_view(), name="template-list-create"),
    path("templates/<uuid:pk>/", TaskTemplateDetailView.as_view(), name="template-detail"),
    path("lists/", TaskListListCreateView.as_view(), name="list-list-create"),
    path("lists/<uuid:pk>/", TaskListDetailView.as_view(), name="list-detail"),
    path("lists/<uuid:pk>/duplicate/", TaskListDuplicateView.as_view(), name="list-duplicate"),
    path("lists/<uuid:pk>/reorder/", TaskListReorderView.as_view(), name="list-reorder"),
    path("lists/<uuid:pk>/usage/", TaskListUsageView.as_view(), name="list-usage"),
    # Recurring schedules
    path("schedules/", RecurringScheduleListCreateView.as_view(), name="schedule-list-create"),
    path("schedules/<uuid:pk>/", RecurringScheduleDetailView.as_view(), name="schedule-detail"),
    path("schedules/<uuid:pk>/runs/", RecurringScheduleRunsView.as_view(), name="schedule-runs"),
    path("schedules/<uuid:pk>/trigger/", RecurringScheduleTriggerView.as_view(), name="schedule-trigger"),
]
