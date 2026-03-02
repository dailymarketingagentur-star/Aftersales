from django.contrib import admin

from apps.tasks.models import (
    ClientActivity,
    RecurringTaskRun,
    RecurringTaskSchedule,
    Subtask,
    Task,
    TaskList,
    TaskListItem,
    TaskTemplate,
)


class SubtaskInline(admin.TabularInline):
    model = Subtask
    extra = 0


class TaskListItemInline(admin.TabularInline):
    model = TaskListItem
    extra = 0
    raw_id_fields = ["task_template"]
    fields = ["task_template", "position", "group_label", "group_position", "day_offset"]


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "action_type", "phase", "day_offset", "priority", "is_active"]
    list_filter = ["action_type", "phase", "priority", "is_active", "tenant"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "client", "action_type", "status", "priority", "due_date", "assigned_to", "group_label"]
    list_filter = ["status", "action_type", "priority", "phase"]
    search_fields = ["title", "client__name"]
    raw_id_fields = ["client", "template", "assigned_to", "completed_by", "email_template", "email_sequence", "source_list"]
    inlines = [SubtaskInline]


@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "is_active", "default_for_service_type", "created_at"]
    list_filter = ["is_active", "tenant"]
    search_fields = ["name", "slug"]
    raw_id_fields = ["tenant", "default_for_service_type"]
    inlines = [TaskListItemInline]


@admin.register(ClientActivity)
class ClientActivityAdmin(admin.ModelAdmin):
    list_display = ["client", "activity_type", "author", "created_at"]
    list_filter = ["activity_type"]
    search_fields = ["client__name", "content"]
    raw_id_fields = ["client", "task", "author"]


class RecurringTaskRunInline(admin.TabularInline):
    model = RecurringTaskRun
    extra = 0
    readonly_fields = [
        "status", "started_at", "completed_at",
        "clients_processed", "tasks_created", "tasks_skipped",
        "error_message",
    ]
    fields = readonly_fields
    show_change_link = True
    ordering = ["-started_at"]
    max_num = 10


@admin.register(RecurringTaskSchedule)
class RecurringTaskScheduleAdmin(admin.ModelAdmin):
    list_display = ["__str__", "tenant", "task_list", "frequency", "is_active", "client_scope", "next_run_at"]
    list_filter = ["is_active", "frequency", "client_scope", "tenant"]
    search_fields = ["name", "task_list__name"]
    raw_id_fields = ["tenant", "task_list"]
    inlines = [RecurringTaskRunInline]


@admin.register(RecurringTaskRun)
class RecurringTaskRunAdmin(admin.ModelAdmin):
    list_display = ["schedule", "status", "started_at", "clients_processed", "tasks_created", "tasks_skipped"]
    list_filter = ["status"]
    search_fields = ["schedule__name"]
    raw_id_fields = ["tenant", "schedule"]
    readonly_fields = [
        "tenant", "schedule", "status", "started_at", "completed_at",
        "clients_processed", "tasks_created", "tasks_skipped",
        "error_message", "details",
    ]
