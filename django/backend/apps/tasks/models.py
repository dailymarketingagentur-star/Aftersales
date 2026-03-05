from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.common.models import TimestampedModel, TenantScopedModel


# ---------------------------------------------------------------------------
# TaskTemplate — Bibliothek der moeglichen Aufgaben (System + Tenant)
# ---------------------------------------------------------------------------
class TriggerMode(models.TextChoices):
    MANUAL = "manual", "Manuell"
    AUTO_ON_DUE = "auto_on_due", "Automatisch bei Fälligkeit"


class TaskTemplate(TimestampedModel):
    """Reusable task template. tenant=NULL means system-wide default."""

    class ActionType(models.TextChoices):
        EMAIL = "email", "E-Mail"
        EMAIL_SEQUENCE = "email_sequence", "E-Mail-Sequenz"
        PACKAGE = "package", "Paket"
        PHONE = "phone", "Telefonat"
        MEETING = "meeting", "Meeting"
        DOCUMENT = "document", "Dokument"
        JIRA_PROJECT = "jira_project", "Jira-Projekt"
        JIRA_TICKET = "jira_ticket", "Jira-Ticket"
        WEBHOOK = "webhook", "Webhook"
        HEALTH_CHECK = "health_check", "Health-Check"
        CHURN_CHECK = "churn_check", "Churn-Check"
        WHATSAPP = "whatsapp", "WhatsApp"
        MANUAL = "manual", "Manuell"

    class Priority(models.TextChoices):
        LOW = "low", "Niedrig"
        MEDIUM = "medium", "Mittel"
        HIGH = "high", "Hoch"
        CRITICAL = "critical", "Kritisch"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="task_templates",
        null=True,
        blank=True,
        help_text="NULL = System-Template, gesetzt = mandantenspezifisch.",
    )
    slug = models.SlugField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    action_type = models.CharField(max_length=20, choices=ActionType.choices, default=ActionType.MANUAL)
    phase = models.PositiveSmallIntegerField(
        default=0,
        help_text="After-Sales Phase (0-11).",
    )
    day_offset = models.IntegerField(
        default=0,
        help_text="Tage nach Client-Startdatum fuer die Faelligkeit.",
    )
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    email_template = models.ForeignKey(
        "emails.EmailTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_templates",
        help_text="Verknuepfte E-Mail-Vorlage (Legacy, nicht mehr im Frontend genutzt).",
    )
    email_templates = models.ManyToManyField(
        "emails.EmailTemplate",
        blank=True,
        related_name="task_templates_m2m",
        help_text="Verfuegbare E-Mail-Vorlagen fuer diese Aufgabe.",
    )
    action_template = models.ForeignKey(
        "integrations.ActionTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_templates",
        help_text="Einzelne Jira-Aktion (nur fuer action_type=jira_*).",
    )
    action_sequence = models.ForeignKey(
        "integrations.ActionSequence",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_templates",
        help_text="Jira-Sequenz mit mehreren API-Calls (nur fuer action_type=jira_*).",
    )
    email_sequence = models.ForeignKey(
        "emails.EmailSequence",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_templates_email_seq",
        help_text="E-Mail-Sequenz (nur fuer action_type=email_sequence).",
    )
    default_subtasks = models.JSONField(
        default=list,
        blank=True,
        help_text='Liste von Subtask-Titeln, z.B. ["Adresse pruefen", "Paket packen"].',
    )
    is_active = models.BooleanField(default=True)
    trigger_mode = models.CharField(
        max_length=20,
        choices=TriggerMode.choices,
        default=TriggerMode.MANUAL,
    )

    class Meta(TimestampedModel.Meta):
        ordering = ["phase", "day_offset", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "slug"],
                name="unique_task_template_per_tenant",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(tenant__isnull=True),
                name="unique_system_task_template_slug",
            ),
        ]

    def __str__(self):
        prefix = self.tenant.name if self.tenant else "System"
        return f"[{prefix}] {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            qs = TaskTemplate.objects.filter(tenant=self.tenant)
            while qs.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Task — Konkrete Aufgabe pro Client
# ---------------------------------------------------------------------------
class Task(TenantScopedModel):
    """A concrete task instance linked to a client."""

    class Status(models.TextChoices):
        PLANNED = "planned", "Geplant"
        OPEN = "open", "Offen"
        IN_PROGRESS = "in_progress", "In Bearbeitung"
        COMPLETED = "completed", "Erledigt"
        SKIPPED = "skipped", "Uebersprungen"

    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_instances",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    action_type = models.CharField(
        max_length=20,
        choices=TaskTemplate.ActionType.choices,
        default=TaskTemplate.ActionType.MANUAL,
    )
    phase = models.PositiveSmallIntegerField(default=0)
    priority = models.CharField(
        max_length=20,
        choices=TaskTemplate.Priority.choices,
        default=TaskTemplate.Priority.MEDIUM,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    due_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_tasks",
    )
    email_template = models.ForeignKey(
        "emails.EmailTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    email_templates = models.ManyToManyField(
        "emails.EmailTemplate",
        blank=True,
        related_name="tasks_m2m",
        help_text="Verfuegbare E-Mail-Vorlagen fuer diese Aufgabe.",
    )
    action_template = models.ForeignKey(
        "integrations.ActionTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        help_text="Einzelne Jira-Aktion.",
    )
    action_sequence = models.ForeignKey(
        "integrations.ActionSequence",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        help_text="Jira-Sequenz.",
    )
    email_sequence = models.ForeignKey(
        "emails.EmailSequence",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks_email_seq",
        help_text="E-Mail-Sequenz.",
    )
    notes = models.TextField(blank=True, default="")
    group_label = models.CharField(
        max_length=100, blank=True, default="",
        help_text='Gruppenname aus der Aufgabenliste, z.B. "Setup & Vorbereitung".',
    )
    source_list = models.ForeignKey(
        "tasks.TaskList",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_tasks",
        help_text="Aufgabenliste, aus der diese Aufgabe generiert wurde.",
    )
    trigger_mode = models.CharField(
        max_length=20,
        choices=TriggerMode.choices,
        null=True,
        blank=True,
        help_text="NULL = Template-Default verwenden.",
    )
    auto_trigger_error = models.TextField(blank=True, default="")
    auto_trigger_attempted_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["phase", "due_date", "-priority", "title"]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title} ({self.client.name})"

    @property
    def effective_trigger_mode(self) -> str:
        if self.trigger_mode:
            return self.trigger_mode
        if self.template and self.template.trigger_mode:
            return self.template.trigger_mode
        return TriggerMode.MANUAL


# ---------------------------------------------------------------------------
# Subtask — Checklisten-Items pro Task
# ---------------------------------------------------------------------------
class Subtask(TenantScopedModel):
    """Individual checklist item within a task."""

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="subtasks",
    )
    title = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta(TenantScopedModel.Meta):
        ordering = ["position"]

    def __str__(self):
        check = "x" if self.is_done else " "
        return f"[{check}] {self.title}"


# ---------------------------------------------------------------------------
# TaskList — Benannte Aufgabenliste (Workflow)
# ---------------------------------------------------------------------------
class TaskList(TimestampedModel):
    """Benannte Aufgabenliste (Workflow). tenant=NULL = System-Liste."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="task_lists",
        null=True,
        blank=True,
        help_text="NULL = System-Liste, gesetzt = mandantenspezifisch.",
    )
    slug = models.SlugField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    default_for_service_type = models.ForeignKey(
        "clients.ServiceType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_task_lists",
        help_text="Wenn gesetzt, wird diese Liste als Standard fuer diesen Service-Typ empfohlen.",
    )

    class Meta(TimestampedModel.Meta):
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "slug"],
                name="unique_task_list_per_tenant",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(tenant__isnull=True),
                name="unique_system_task_list_slug",
            ),
        ]

    def __str__(self):
        prefix = self.tenant.name if self.tenant else "System"
        return f"[{prefix}] {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            qs = TaskList.objects.filter(tenant=self.tenant)
            while qs.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class TaskListItem(TimestampedModel):
    """Geordneter Eintrag in einer Aufgabenliste."""

    task_list = models.ForeignKey(
        TaskList,
        on_delete=models.CASCADE,
        related_name="items",
    )
    task_template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        related_name="task_list_items",
    )
    position = models.PositiveIntegerField(default=0)
    group_label = models.CharField(
        max_length=100, blank=True, default="",
        help_text='Gruppenname in der Liste, z.B. "Setup", "Woche 1".',
    )
    group_position = models.PositiveIntegerField(
        default=0,
        help_text="Sortierung der Gruppen innerhalb der Liste.",
    )
    day_offset = models.IntegerField(
        null=True, blank=True,
        help_text="Ueberschreibt den Tag-Offset des Templates.",
    )

    class Meta(TimestampedModel.Meta):
        ordering = ["group_position", "position"]
        constraints = [
            models.UniqueConstraint(
                fields=["task_list", "task_template"],
                name="unique_template_per_list",
            ),
        ]

    def __str__(self):
        return f"#{self.position} {self.task_template.name} in {self.task_list.name}"


# ---------------------------------------------------------------------------
# ClientActivity — Timeline (inkl. Kommentare als type="comment")
# ---------------------------------------------------------------------------
class ClientActivity(TenantScopedModel):
    """Timeline entry for a client. Comments are activity_type='comment'."""

    class ActivityType(models.TextChoices):
        COMMENT = "comment", "Kommentar"
        TASK_CREATED = "task_created", "Aufgabe erstellt"
        TASK_COMPLETED = "task_completed", "Aufgabe erledigt"
        TASK_SKIPPED = "task_skipped", "Aufgabe uebersprungen"
        STATUS_CHANGED = "status_changed", "Status geaendert"
        EMAIL_SENT = "email_sent", "E-Mail gesendet"
        JIRA_EXECUTED = "jira_executed", "Jira-Aktion ausgefuehrt"
        WEBHOOK_EXECUTED = "webhook_executed", "Webhook ausgefuehrt"
        NPS_SENT = "nps_sent", "NPS-Umfrage gesendet"
        NPS_RECEIVED = "nps_received", "NPS erhalten"
        AUTO_TRIGGER_SUCCESS = "auto_trigger_success", "Auto-Trigger erfolgreich"
        AUTO_TRIGGER_FAILED = "auto_trigger_failed", "Auto-Trigger fehlgeschlagen"
        LIST_REMOVED = "list_removed", "Aufgabenliste entfernt"
        HEALTH_CHECK_COMPLETED = "health_check_completed", "Health-Check ausgefuellt"
        CHURN_CHECK_COMPLETED = "churn_check_completed", "Churn-Check ausgefuellt"
        WHATSAPP_SENT = "whatsapp_sent", "WhatsApp gesendet"

    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="activities",
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    content = models.TextField(blank=True, default="", help_text="Kommentartext oder automatische Beschreibung.")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_activities",
    )

    class Meta(TenantScopedModel.Meta):
        verbose_name_plural = "Client activities"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_activity_type_display()}] {self.client.name}"


# ---------------------------------------------------------------------------
# RecurringTaskSchedule — Wiederkehrender Zeitplan pro TaskList
# ---------------------------------------------------------------------------
class RecurringTaskSchedule(TenantScopedModel):
    """Defines a recurring schedule to auto-generate tasks from a TaskList."""

    class Frequency(models.TextChoices):
        WEEKLY = "weekly", "Woechentlich"
        BIWEEKLY = "biweekly", "Alle 2 Wochen"
        MONTHLY = "monthly", "Monatlich"
        QUARTERLY = "quarterly", "Quartalsweise"

    class ClientScope(models.TextChoices):
        ALL_ACTIVE = "all_active", "Alle aktiven Clients"
        BY_SERVICE_TYPE = "by_service_type", "Nach Service-Typ"
        EXPLICIT = "explicit", "Explizite Auswahl"

    task_list = models.ForeignKey(
        TaskList,
        on_delete=models.CASCADE,
        related_name="recurring_schedules",
    )
    name = models.CharField(max_length=255, blank=True, default="")
    frequency = models.CharField(max_length=20, choices=Frequency.choices)
    is_active = models.BooleanField(default=True)
    client_scope = models.CharField(
        max_length=20,
        choices=ClientScope.choices,
        default=ClientScope.ALL_ACTIVE,
    )
    service_types = models.ManyToManyField(
        "clients.ServiceType",
        blank=True,
        related_name="recurring_schedules",
        help_text="Nur bei client_scope=by_service_type.",
    )
    clients = models.ManyToManyField(
        "clients.Client",
        blank=True,
        related_name="recurring_schedules",
        help_text="Nur bei client_scope=explicit.",
    )
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta(TenantScopedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "task_list"],
                name="unique_schedule_per_list_per_tenant",
            ),
        ]
        indexes = [
            models.Index(
                fields=["is_active", "next_run_at"],
                name="idx_schedule_active_next_run",
            ),
        ]

    def __str__(self):
        label = self.name or self.task_list.name
        return f"[{self.get_frequency_display()}] {label}"


# ---------------------------------------------------------------------------
# RecurringTaskRun — Audit-Log pro Ausfuehrung
# ---------------------------------------------------------------------------
class RecurringTaskRun(TenantScopedModel):
    """Audit record for a single execution of a RecurringTaskSchedule."""

    class Status(models.TextChoices):
        SUCCESS = "success", "Erfolgreich"
        PARTIAL = "partial", "Teilweise"
        FAILED = "failed", "Fehlgeschlagen"
        SKIPPED = "skipped", "Uebersprungen"

    schedule = models.ForeignKey(
        RecurringTaskSchedule,
        on_delete=models.CASCADE,
        related_name="runs",
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    clients_processed = models.PositiveIntegerField(default=0)
    tasks_created = models.PositiveIntegerField(default=0)
    tasks_skipped = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    details = models.JSONField(default=dict, blank=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["-started_at"]

    def __str__(self):
        return f"Run {self.started_at:%Y-%m-%d %H:%M} — {self.get_status_display()}"
