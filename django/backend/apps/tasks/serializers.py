from rest_framework import serializers

from apps.emails.models import EmailTemplate
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


# ---------------------------------------------------------------------------
# EmailTemplate Summary (lightweight fuer Dropdowns)
# ---------------------------------------------------------------------------
class EmailTemplateSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = ["id", "slug", "name", "subject"]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# TaskTemplate
# ---------------------------------------------------------------------------
class TaskTemplateSerializer(serializers.ModelSerializer):
    is_system = serializers.SerializerMethodField()
    email_templates_detail = EmailTemplateSummarySerializer(source="email_templates", many=True, read_only=True)
    action_template_slug = serializers.SlugField(source="action_template.slug", read_only=True, default=None)
    action_sequence_slug = serializers.SlugField(source="action_sequence.slug", read_only=True, default=None)
    action_template_id = serializers.UUIDField(source="action_template.id", read_only=True, default=None)
    action_sequence_id = serializers.UUIDField(source="action_sequence.id", read_only=True, default=None)
    email_sequence_slug = serializers.SlugField(source="email_sequence.slug", read_only=True, default=None)
    email_sequence_id = serializers.UUIDField(source="email_sequence.id", read_only=True, default=None)

    class Meta:
        model = TaskTemplate
        fields = [
            "id", "slug", "name", "description", "action_type", "phase",
            "day_offset", "priority", "email_template", "default_subtasks",
            "is_active", "trigger_mode", "is_system",
            "email_templates_detail", "action_template_slug", "action_sequence_slug",
            "action_template_id", "action_sequence_id",
            "email_sequence_slug", "email_sequence_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_is_system(self, obj):
        return obj.tenant is None


class TaskTemplateCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default="")
    action_type = serializers.ChoiceField(
        choices=TaskTemplate.ActionType.choices, required=False, default="manual"
    )
    phase = serializers.IntegerField(required=False, default=0, min_value=0, max_value=11)
    day_offset = serializers.IntegerField(required=False, default=0)
    priority = serializers.ChoiceField(
        choices=TaskTemplate.Priority.choices, required=False, default="medium"
    )
    email_template = serializers.UUIDField(required=False, allow_null=True, default=None)
    action_template = serializers.UUIDField(required=False, allow_null=True, default=None)
    action_sequence = serializers.UUIDField(required=False, allow_null=True, default=None)
    email_sequence = serializers.UUIDField(required=False, allow_null=True, default=None)
    default_subtasks = serializers.ListField(
        child=serializers.CharField(max_length=255),
        required=False,
        default=list,
    )
    is_active = serializers.BooleanField(required=False, default=True)


# ---------------------------------------------------------------------------
# Subtask
# ---------------------------------------------------------------------------
class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = ["id", "title", "is_done", "position", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------
class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubtaskSerializer(many=True, read_only=True)
    assigned_to_email = serializers.EmailField(source="assigned_to.email", read_only=True, default=None)
    completed_by_email = serializers.EmailField(source="completed_by.email", read_only=True, default=None)
    template_name = serializers.CharField(source="template.name", read_only=True, default=None)
    email_templates_detail = EmailTemplateSummarySerializer(source="email_templates", many=True, read_only=True)
    action_template_slug = serializers.SlugField(source="action_template.slug", read_only=True, default=None)
    action_sequence_slug = serializers.SlugField(source="action_sequence.slug", read_only=True, default=None)
    action_template_id = serializers.UUIDField(source="action_template.id", read_only=True, default=None)
    action_sequence_id = serializers.UUIDField(source="action_sequence.id", read_only=True, default=None)
    email_sequence_slug = serializers.SlugField(source="email_sequence.slug", read_only=True, default=None)
    email_sequence_id = serializers.UUIDField(source="email_sequence.id", read_only=True, default=None)

    source_list_id = serializers.UUIDField(source="source_list.id", read_only=True, default=None)
    source_list_name = serializers.CharField(source="source_list.name", read_only=True, default=None)

    effective_trigger_mode = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "client", "template", "template_name",
            "title", "description", "action_type", "phase", "priority",
            "status", "due_date", "assigned_to", "assigned_to_email",
            "completed_at", "completed_by", "completed_by_email",
            "email_template", "notes", "group_label",
            "source_list_id", "source_list_name",
            "trigger_mode", "effective_trigger_mode",
            "auto_trigger_error", "auto_trigger_attempted_at",
            "email_templates_detail", "action_template_slug", "action_sequence_slug",
            "action_template_id", "action_sequence_id",
            "email_sequence_slug", "email_sequence_id",
            "subtasks",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "client", "template", "completed_at", "completed_by",
            "auto_trigger_error", "auto_trigger_attempted_at",
            "created_at", "updated_at",
        ]

    def get_effective_trigger_mode(self, obj):
        return obj.effective_trigger_mode


class TaskCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default="")
    action_type = serializers.ChoiceField(
        choices=TaskTemplate.ActionType.choices, required=False, default="manual"
    )
    phase = serializers.IntegerField(required=False, default=0, min_value=0, max_value=11)
    priority = serializers.ChoiceField(
        choices=TaskTemplate.Priority.choices, required=False, default="medium"
    )
    due_date = serializers.DateField(required=False, allow_null=True, default=None)
    assigned_to = serializers.UUIDField(required=False, allow_null=True, default=None)
    email_template = serializers.UUIDField(required=False, allow_null=True, default=None)
    notes = serializers.CharField(required=False, default="")
    subtasks = serializers.ListField(
        child=serializers.CharField(max_length=255),
        required=False,
        default=list,
    )


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "title", "description", "priority", "due_date",
            "assigned_to", "notes", "trigger_mode",
        ]


class GenerateTasksSerializer(serializers.Serializer):
    template_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
        help_text="Spezifische Template-IDs. Leer = alle aktiven Templates.",
    )
    task_list_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Aufgabenliste-ID. Wenn gesetzt, werden Templates aus der Liste verwendet.",
    )


# ---------------------------------------------------------------------------
# ClientActivity
# ---------------------------------------------------------------------------
class ClientActivitySerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True, default=None)
    task_title = serializers.CharField(source="task.title", read_only=True, default=None)

    class Meta:
        model = ClientActivity
        fields = [
            "id", "client", "task", "task_title",
            "activity_type", "content",
            "author", "author_email",
            "created_at",
        ]
        read_only_fields = ["id", "client", "task", "author", "created_at"]


# ---------------------------------------------------------------------------
# Email-Aktionen aus Tasks heraus
# ---------------------------------------------------------------------------
class TaskEmailPreviewSerializer(serializers.Serializer):
    template_slug = serializers.SlugField()


class TaskSendEmailSerializer(serializers.Serializer):
    template_slug = serializers.SlugField()


# ---------------------------------------------------------------------------
# Kommentare
# ---------------------------------------------------------------------------
class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField()
    task = serializers.UUIDField(required=False, allow_null=True, default=None)


# ---------------------------------------------------------------------------
# TaskList / TaskListItem
# ---------------------------------------------------------------------------
class TaskListItemSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="task_template.name", read_only=True)
    template_slug = serializers.SlugField(source="task_template.slug", read_only=True)
    action_type = serializers.CharField(source="task_template.action_type", read_only=True)
    phase = serializers.IntegerField(source="task_template.phase", read_only=True)
    template_day_offset = serializers.IntegerField(source="task_template.day_offset", read_only=True)
    priority = serializers.CharField(source="task_template.priority", read_only=True)

    class Meta:
        model = TaskListItem
        fields = [
            "id", "task_template", "template_name", "template_slug",
            "action_type", "phase", "template_day_offset", "priority",
            "position", "group_label", "group_position", "day_offset",
        ]


class TaskListSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    is_system = serializers.SerializerMethodField()
    default_for_service_type = serializers.UUIDField(
        source="default_for_service_type.id", read_only=True, default=None,
    )
    default_for_service_type_name = serializers.CharField(
        source="default_for_service_type.name", read_only=True, default=None,
    )

    class Meta:
        model = TaskList
        fields = [
            "id", "slug", "name", "description", "is_active",
            "default_for_service_type", "default_for_service_type_name",
            "items", "item_count", "is_system", "created_at", "updated_at",
        ]

    def get_items(self, obj):
        items = obj.items.order_by("group_position", "position").select_related("task_template")
        return TaskListItemSerializer(items, many=True).data

    def get_item_count(self, obj):
        return obj.items.count()

    def get_is_system(self, obj):
        return obj.tenant is None


class TaskListCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default="")
    template_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
    )


class TaskListReorderSerializer(serializers.Serializer):
    item_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="Item-IDs in gewuenschter Reihenfolge.",
    )


# ---------------------------------------------------------------------------
# Remove List from Client
# ---------------------------------------------------------------------------
class RemoveListSerializer(serializers.Serializer):
    task_list_id = serializers.UUIDField()


# ---------------------------------------------------------------------------
# RecurringTaskSchedule
# ---------------------------------------------------------------------------
class RecurringTaskScheduleSerializer(serializers.ModelSerializer):
    """Read serializer with enriched display fields."""

    task_list_name = serializers.CharField(source="task_list.name", read_only=True)
    last_run_summary = serializers.SerializerMethodField()
    service_type_ids = serializers.PrimaryKeyRelatedField(
        source="service_types", many=True, read_only=True,
    )
    client_ids = serializers.PrimaryKeyRelatedField(
        source="clients", many=True, read_only=True,
    )

    class Meta:
        model = RecurringTaskSchedule
        fields = [
            "id", "task_list", "task_list_name", "name",
            "frequency", "is_active", "client_scope",
            "service_type_ids", "client_ids",
            "last_run_at", "next_run_at",
            "last_run_summary",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_last_run_summary(self, obj):
        last_run = obj.runs.order_by("-started_at").first()
        if not last_run:
            return None
        return {
            "status": last_run.status,
            "started_at": last_run.started_at.isoformat(),
            "tasks_created": last_run.tasks_created,
            "clients_processed": last_run.clients_processed,
        }


class RecurringTaskScheduleCreateSerializer(serializers.Serializer):
    """Write serializer for creating / updating a schedule."""

    task_list_id = serializers.UUIDField()
    name = serializers.CharField(max_length=255, required=False, default="")
    frequency = serializers.ChoiceField(choices=RecurringTaskSchedule.Frequency.choices)
    is_active = serializers.BooleanField(required=False, default=True)
    client_scope = serializers.ChoiceField(
        choices=RecurringTaskSchedule.ClientScope.choices,
        required=False,
        default="all_active",
    )
    service_type_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list,
    )
    client_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list,
    )


class RecurringTaskRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringTaskRun
        fields = [
            "id", "schedule", "status",
            "started_at", "completed_at",
            "clients_processed", "tasks_created", "tasks_skipped",
            "error_message", "details",
            "created_at",
        ]
        read_only_fields = fields
