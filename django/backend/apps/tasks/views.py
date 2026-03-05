from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import Client
from apps.common.permissions import HasActiveSubscription, IsTenantAdmin, IsTenantMember
from apps.emails.models import EmailProviderConnection, EmailSequence, EmailTemplate
from apps.emails.services import EmailService
from apps.integrations.models import ActionSequence, ActionTemplate
from apps.integrations.services import IntegrationService
from apps.tasks.models import (
    ClientActivity,
    RecurringTaskSchedule,
    Subtask,
    Task,
    TaskList,
    TaskListItem,
    TaskTemplate,
)
from apps.tasks.serializers import (
    ClientActivitySerializer,
    CommentCreateSerializer,
    GenerateTasksSerializer,
    RecurringTaskRunSerializer,
    RecurringTaskScheduleCreateSerializer,
    RecurringTaskScheduleSerializer,
    SubtaskSerializer,
    TaskCreateSerializer,
    TaskDashboardSerializer,
    TaskEmailPreviewSerializer,
    TaskListCreateSerializer,
    TaskListReorderSerializer,
    TaskListSerializer,
    TaskSendEmailSerializer,
    TaskSerializer,
    TaskTemplateCreateSerializer,
    TaskTemplateSerializer,
    TaskUpdateSerializer,
)
from apps.tasks.services import TaskService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_client(request, slug):
    try:
        return Client.objects.get(tenant=request.tenant, slug=slug)
    except Client.DoesNotExist:
        return None


def _not_found(name="Mandant"):
    return Response({"detail": f"{name} nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)


def _build_client_context(client, tenant):
    """Standard-Kontext fuer Email/Jira-Rendering aus Client-Daten."""
    return {
        "FIRST_NAME": client.contact_first_name or client.name.split()[0] if client.name else "",
        "LAST_NAME": client.contact_last_name or "",
        "CLIENT_NAME": client.name,
        "KUNDENNAME": client.name,
        "FIRMENNAME": client.name,
        "TENANT_NAME": tenant.name if tenant else "",
    }


# ---------------------------------------------------------------------------
# Dashboard — /api/v1/tasks/dashboard/
# ---------------------------------------------------------------------------
class TaskDashboardView(APIView):
    """Aufgaben ueber alle Clients eines Tenants (fuer Dashboard)."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request):
        from django.db.models import Case, Value, When

        qs = (
            Task.objects.filter(tenant=request.tenant)
            .select_related("client", "assigned_to")
        )

        # Filter: ?status=open,in_progress
        status_param = request.query_params.get("status")
        if status_param:
            statuses = [s.strip() for s in status_param.split(",") if s.strip()]
            qs = qs.filter(status__in=statuses)

        # Filter: ?due_date=today|future
        due_date_param = request.query_params.get("due_date")
        if due_date_param == "today":
            qs = qs.filter(due_date=timezone.localdate())
        elif due_date_param == "future":
            qs = qs.filter(due_date__gt=timezone.localdate())

        # Sortierung: due_date ASC (nulls last), dann Priority
        priority_order = Case(
            When(priority="critical", then=Value(0)),
            When(priority="high", then=Value(1)),
            When(priority="medium", then=Value(2)),
            When(priority="low", then=Value(3)),
        )
        qs = qs.order_by(
            models.F("due_date").asc(nulls_last=True),
            priority_order,
        )

        serializer = TaskDashboardSerializer(qs, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# TaskTemplate views — /api/v1/tasks/templates/
# ---------------------------------------------------------------------------
class TaskTemplateListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def get(self, request):
        qs = TaskTemplate.objects.filter(
            Q(tenant=request.tenant) | Q(tenant__isnull=True),
            is_active=True,
        ).select_related(
            "action_template", "action_sequence", "email_sequence",
        ).prefetch_related("email_templates")
        serializer = TaskTemplateSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TaskTemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        email_tpl_id = data.pop("email_template", None)
        email_tpl = None
        if email_tpl_id:
            try:
                email_tpl = EmailTemplate.objects.get(
                    Q(tenant=request.tenant) | Q(tenant__isnull=True),
                    id=email_tpl_id,
                )
            except EmailTemplate.DoesNotExist:
                return Response(
                    {"detail": "E-Mail-Vorlage nicht gefunden."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        action_tpl_id = data.pop("action_template", None)
        action_tpl = None
        if action_tpl_id:
            try:
                action_tpl = ActionTemplate.objects.get(
                    Q(tenant=request.tenant) | Q(tenant__isnull=True),
                    id=action_tpl_id, is_active=True,
                )
            except ActionTemplate.DoesNotExist:
                return Response(
                    {"detail": "Jira-Aktionsvorlage nicht gefunden."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        action_seq_id = data.pop("action_sequence", None)
        action_seq = None
        if action_seq_id:
            try:
                action_seq = ActionSequence.objects.get(
                    Q(tenant=request.tenant) | Q(tenant__isnull=True),
                    id=action_seq_id, is_active=True,
                )
            except ActionSequence.DoesNotExist:
                return Response(
                    {"detail": "Jira-Sequenz nicht gefunden."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        email_seq_id = data.pop("email_sequence", None)
        email_seq = None
        if email_seq_id:
            try:
                email_seq = EmailSequence.objects.get(
                    Q(tenant=request.tenant) | Q(tenant__isnull=True),
                    id=email_seq_id, is_active=True,
                )
            except EmailSequence.DoesNotExist:
                return Response(
                    {"detail": "E-Mail-Sequenz nicht gefunden."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        tpl = TaskTemplate(
            tenant=request.tenant,
            email_template=email_tpl,
            action_template=action_tpl,
            action_sequence=action_seq,
            email_sequence=email_seq,
            **data,
        )
        tpl.save()
        return Response(TaskTemplateSerializer(tpl).data, status=status.HTTP_201_CREATED)


class TaskTemplateDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def _get_template(self, request, pk):
        try:
            return TaskTemplate.objects.get(
                Q(tenant=request.tenant) | Q(tenant__isnull=True),
                pk=pk,
            )
        except TaskTemplate.DoesNotExist:
            return None

    def get(self, request, pk):
        tpl = self._get_template(request, pk)
        if tpl is None:
            return _not_found("Aufgaben-Vorlage")
        return Response(TaskTemplateSerializer(tpl).data)

    def patch(self, request, pk):
        tpl = self._get_template(request, pk)
        if tpl is None:
            return _not_found("Aufgaben-Vorlage")
        serializer = TaskTemplateCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        # FK-Felder separat aufloesen (setattr mit UUID funktioniert nicht fuer FKs)
        for fk_field, model_cls, label in [
            ("action_template", ActionTemplate, "Jira-Aktionsvorlage"),
            ("action_sequence", ActionSequence, "Jira-Sequenz"),
            ("email_sequence", EmailSequence, "E-Mail-Sequenz"),
        ]:
            if fk_field in vd:
                fk_id = vd.pop(fk_field)
                if fk_id:
                    try:
                        obj = model_cls.objects.get(
                            Q(tenant=request.tenant) | Q(tenant__isnull=True),
                            id=fk_id, is_active=True,
                        )
                    except model_cls.DoesNotExist:
                        return Response(
                            {"detail": f"{label} nicht gefunden."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    setattr(tpl, fk_field, obj)
                else:
                    setattr(tpl, fk_field, None)

        for key, value in vd.items():
            setattr(tpl, key, value)
        tpl.save()
        return Response(TaskTemplateSerializer(tpl).data)

    def delete(self, request, pk):
        tpl = self._get_template(request, pk)
        if tpl is None:
            return _not_found("Aufgaben-Vorlage")
        tpl.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Task views — /api/v1/clients/<slug>/tasks/
# ---------------------------------------------------------------------------
class TaskListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def get(self, request, slug):
        client = _get_client(request, slug)
        if client is None:
            return _not_found()

        qs = Task.objects.filter(client=client).select_related(
            "template", "assigned_to", "completed_by", "email_template",
            "action_template", "action_sequence", "email_sequence", "source_list",
        ).prefetch_related("subtasks", "email_templates")

        # Filter by status
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Filter by phase
        phase_filter = request.query_params.get("phase")
        if phase_filter is not None:
            qs = qs.filter(phase=phase_filter)

        serializer = TaskSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request, slug):
        client = _get_client(request, slug)
        if client is None:
            return _not_found()

        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        subtask_titles = data.pop("subtasks", [])
        assigned_to_id = data.pop("assigned_to", None)
        email_tpl_id = data.pop("email_template", None)

        task = Task.objects.create(
            tenant=request.tenant,
            client=client,
            assigned_to_id=assigned_to_id,
            email_template_id=email_tpl_id,
            **data,
        )

        for i, title in enumerate(subtask_titles):
            Subtask.objects.create(
                tenant=request.tenant, task=task, title=title, position=i,
            )

        # Timeline-Eintrag
        ClientActivity.objects.create(
            tenant=request.tenant,
            client=client,
            task=task,
            activity_type=ClientActivity.ActivityType.TASK_CREATED,
            content=f'Aufgabe "{task.title}" erstellt.',
            author=request.user,
        )

        task.refresh_from_db()
        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_201_CREATED,
        )


class TaskDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def _get_task(self, request, slug, pk):
        try:
            return Task.objects.select_related(
                "template", "assigned_to", "completed_by", "email_template",
                "action_template", "action_sequence", "email_sequence", "client", "source_list",
            ).prefetch_related("subtasks", "email_templates").get(
                client__tenant=request.tenant, client__slug=slug, pk=pk,
            )
        except Task.DoesNotExist:
            return None

    def get(self, request, slug, pk):
        task = self._get_task(request, slug, pk)
        if task is None:
            return _not_found("Aufgabe")
        return Response(TaskSerializer(task).data)

    def patch(self, request, slug, pk):
        task = self._get_task(request, slug, pk)
        if task is None:
            return _not_found("Aufgabe")

        serializer = TaskUpdateSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TaskSerializer(task).data)

    def delete(self, request, slug, pk):
        task = self._get_task(request, slug, pk)
        if task is None:
            return _not_found("Aufgabe")
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Task actions — complete, skip
# ---------------------------------------------------------------------------
class TaskCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def post(self, request, slug, pk):
        client = _get_client(request, slug)
        if client is None:
            return _not_found()
        try:
            task = Task.objects.get(client=client, pk=pk)
        except Task.DoesNotExist:
            return _not_found("Aufgabe")

        if task.status == Task.Status.COMPLETED:
            return Response({"detail": "Aufgabe ist bereits erledigt."}, status=status.HTTP_400_BAD_REQUEST)

        task.status = Task.Status.COMPLETED
        task.completed_at = timezone.now()
        task.completed_by = request.user
        task.save(update_fields=["status", "completed_at", "completed_by", "updated_at"])

        ClientActivity.objects.create(
            tenant=request.tenant,
            client=client,
            task=task,
            activity_type=ClientActivity.ActivityType.TASK_COMPLETED,
            content=f'Aufgabe "{task.title}" erledigt.',
            author=request.user,
        )

        return Response(TaskSerializer(task).data)


class TaskSkipView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def post(self, request, slug, pk):
        client = _get_client(request, slug)
        if client is None:
            return _not_found()
        try:
            task = Task.objects.get(client=client, pk=pk)
        except Task.DoesNotExist:
            return _not_found("Aufgabe")

        task.status = Task.Status.SKIPPED
        task.save(update_fields=["status", "updated_at"])

        ClientActivity.objects.create(
            tenant=request.tenant,
            client=client,
            task=task,
            activity_type=ClientActivity.ActivityType.TASK_SKIPPED,
            content=f'Aufgabe "{task.title}" uebersprungen.',
            author=request.user,
        )

        return Response(TaskSerializer(task).data)


# ---------------------------------------------------------------------------
# TaskList views — /api/v1/tasks/lists/
# ---------------------------------------------------------------------------
class TaskListListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def get(self, request):
        qs = TaskList.objects.filter(
            Q(tenant=request.tenant) | Q(tenant__isnull=True),
            is_active=True,
        ).select_related(
            "default_for_service_type",
        ).prefetch_related(
            "items__task_template",
        )
        # Optional: nach Service-Typ filtern
        service_type = request.query_params.get("service_type")
        if service_type:
            qs = qs.filter(default_for_service_type_id=service_type)
        serializer = TaskListSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TaskListCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        template_ids = data.pop("template_ids", [])

        task_list = TaskList(tenant=request.tenant, **data)
        task_list.save()

        # Items erstellen aus template_ids (Reihenfolge = Array-Index)
        # Optional: items-Array mit erweiterten Feldern (group_label, group_position, day_offset)
        items_data = request.data.get("items")
        if items_data and isinstance(items_data, list):
            # Neues Format: [{template_id, group_label, group_position, day_offset}, ...]
            all_tpl_ids = [item.get("template_id") for item in items_data if item.get("template_id")]
            templates = TaskTemplate.objects.filter(
                Q(tenant=request.tenant) | Q(tenant__isnull=True),
                id__in=all_tpl_ids,
                is_active=True,
            )
            tpl_map = {str(t.id): t for t in templates}
            for i, item_data in enumerate(items_data):
                tpl = tpl_map.get(str(item_data.get("template_id")))
                if tpl:
                    TaskListItem.objects.create(
                        task_list=task_list,
                        task_template=tpl,
                        position=i,
                        group_label=item_data.get("group_label", ""),
                        group_position=item_data.get("group_position", 0),
                        day_offset=item_data.get("day_offset"),
                    )
        elif template_ids:
            templates = TaskTemplate.objects.filter(
                Q(tenant=request.tenant) | Q(tenant__isnull=True),
                id__in=template_ids,
                is_active=True,
            )
            tpl_map = {str(t.id): t for t in templates}
            for i, tid in enumerate(template_ids):
                tpl = tpl_map.get(str(tid))
                if tpl:
                    TaskListItem.objects.create(
                        task_list=task_list, task_template=tpl, position=i,
                    )

        return Response(
            TaskListSerializer(task_list).data,
            status=status.HTTP_201_CREATED,
        )


class TaskListDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def _get_list(self, request, pk):
        try:
            return TaskList.objects.prefetch_related(
                "items__task_template",
            ).get(
                Q(tenant=request.tenant) | Q(tenant__isnull=True),
                pk=pk,
            )
        except TaskList.DoesNotExist:
            return None

    def get(self, request, pk):
        task_list = self._get_list(request, pk)
        if task_list is None:
            return _not_found("Aufgabenliste")
        return Response(TaskListSerializer(task_list).data)

    def patch(self, request, pk):
        task_list = self._get_list(request, pk)
        if task_list is None:
            return _not_found("Aufgabenliste")
        if task_list.tenant is None:
            return Response(
                {"detail": "System-Listen koennen nicht bearbeitet werden."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Name/Description updaten
        if "name" in request.data:
            task_list.name = request.data["name"]
        if "description" in request.data:
            task_list.description = request.data["description"]
        # default_for_service_type updaten
        if "default_for_service_type" in request.data:
            st_id = request.data["default_for_service_type"]
            task_list.default_for_service_type_id = st_id if st_id else None
        task_list.save()

        # Items ersetzen wenn template_ids mitgegeben
        template_ids = request.data.get("template_ids")
        if template_ids is not None:
            task_list.items.all().delete()
            templates = TaskTemplate.objects.filter(
                Q(tenant=request.tenant) | Q(tenant__isnull=True),
                id__in=template_ids,
                is_active=True,
            )
            tpl_map = {str(t.id): t for t in templates}
            for i, tid in enumerate(template_ids):
                tpl = tpl_map.get(str(tid))
                if tpl:
                    TaskListItem.objects.create(
                        task_list=task_list, task_template=tpl, position=i,
                    )

        # Einzelnes Item-Update: group_label, day_offset
        item_updates = request.data.get("item_updates")
        if item_updates and isinstance(item_updates, list):
            for upd in item_updates:
                item_id = upd.get("id")
                if not item_id:
                    continue
                try:
                    item = TaskListItem.objects.get(pk=item_id, task_list=task_list)
                except TaskListItem.DoesNotExist:
                    continue
                if "group_label" in upd:
                    item.group_label = upd["group_label"]
                if "group_position" in upd:
                    item.group_position = upd["group_position"]
                if "day_offset" in upd:
                    item.day_offset = upd["day_offset"]
                item.save()

        task_list.refresh_from_db()
        return Response(TaskListSerializer(task_list).data)

    def delete(self, request, pk):
        task_list = self._get_list(request, pk)
        if task_list is None:
            return _not_found("Aufgabenliste")
        if task_list.tenant is None:
            return Response(
                {"detail": "System-Listen koennen nicht geloescht werden."},
                status=status.HTTP_403_FORBIDDEN,
            )
        task_list.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Generate tasks from templates
# ---------------------------------------------------------------------------
class TaskGenerateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def post(self, request, slug):
        client = _get_client(request, slug)
        if client is None:
            return _not_found()

        serializer = GenerateTasksSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task_list_id = serializer.validated_data.get("task_list_id")

        if not task_list_id:
            return Response(
                {"detail": "task_list_id ist erforderlich."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            task_list = TaskList.objects.get(
                Q(tenant=request.tenant) | Q(tenant__isnull=True),
                pk=task_list_id,
            )
        except TaskList.DoesNotExist:
            return Response(
                {"detail": "Aufgabenliste nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        created_tasks = TaskService.generate_tasks_for_client(
            tenant=request.tenant,
            client=client,
            task_list=task_list,
            author=request.user,
        )

        out = TaskSerializer(created_tasks, many=True)
        return Response(out.data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Subtask toggle — PATCH /api/v1/clients/<slug>/tasks/<pk>/subtasks/<subtask_pk>/
# ---------------------------------------------------------------------------
class SubtaskToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def patch(self, request, slug, pk, subtask_pk):
        client = _get_client(request, slug)
        if client is None:
            return _not_found()
        try:
            subtask = Subtask.objects.select_related("task").get(
                task__client=client, task__pk=pk, pk=subtask_pk,
            )
        except Subtask.DoesNotExist:
            return _not_found("Subtask")

        # Toggle oder explizit setzen
        is_done = request.data.get("is_done")
        if is_done is not None:
            subtask.is_done = is_done
        else:
            subtask.is_done = not subtask.is_done
        subtask.save(update_fields=["is_done", "updated_at"])

        return Response(SubtaskSerializer(subtask).data)


# ---------------------------------------------------------------------------
# Email-Preview aus Task heraus
# ---------------------------------------------------------------------------
class TaskEmailPreviewView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def post(self, request, slug, pk):
        client = _get_client(request, slug)
        if client is None:
            return _not_found()
        try:
            task = Task.objects.select_related("client").prefetch_related("email_templates").get(
                client=client, pk=pk,
            )
        except Task.DoesNotExist:
            return _not_found("Aufgabe")

        serializer = TaskEmailPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template_slug = serializer.validated_data["template_slug"]

        # Pruefen ob das Template zur Aufgabe gehoert
        if not task.email_templates.filter(slug=template_slug).exists():
            return Response(
                {"detail": "E-Mail-Vorlage ist nicht mit dieser Aufgabe verknuepft."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            email_tpl = EmailService._resolve_template(request.tenant, template_slug)
        except Exception:
            return Response(
                {"detail": "E-Mail-Vorlage nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        context = _build_client_context(client, request.tenant)

        rendered_subject = EmailService._render(email_tpl.subject, context)
        rendered_body = EmailService._render(email_tpl.body_html, context)

        return Response({
            "template_slug": email_tpl.slug,
            "template_name": email_tpl.name,
            "subject": rendered_subject,
            "body_html": rendered_body,
            "recipient_email": client.contact_email or "",
        })


# ---------------------------------------------------------------------------
# Email senden aus Task heraus
# ---------------------------------------------------------------------------
class TaskSendEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def post(self, request, slug, pk):
        if not EmailProviderConnection.objects.filter(tenant=request.tenant, is_active=True).exists():
            return Response(
                {"detail": "Kein E-Mail-Provider konfiguriert. Bitte richte SMTP oder SendGrid unter Integrationen → E-Mail ein."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        client = _get_client(request, slug)
        if client is None:
            return _not_found()
        try:
            task = Task.objects.select_related("client").prefetch_related("email_templates").get(
                client=client, pk=pk,
            )
        except Task.DoesNotExist:
            return _not_found("Aufgabe")

        serializer = TaskSendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template_slug = serializer.validated_data["template_slug"]

        if not task.email_templates.filter(slug=template_slug).exists():
            return Response(
                {"detail": "E-Mail-Vorlage ist nicht mit dieser Aufgabe verknuepft."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipient_email = client.contact_email
        if not recipient_email:
            return Response(
                {"detail": "Mandant hat keine E-Mail-Adresse hinterlegt."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # NPS-spezifisch: Bei nps-review Template wird NPSService.send_survey()
        # verwendet, damit ein Survey mit Token erstellt wird statt nur eine
        # generische E-Mail.
        if template_slug == "nps-review":
            from apps.nps.services import NPSService

            try:
                NPSService.send_survey(tenant=request.tenant, client=client, task=task)
            except Exception as e:
                return Response(
                    {"detail": f"NPS-Umfrage konnte nicht gesendet werden: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            ClientActivity.objects.create(
                tenant=request.tenant,
                client=client,
                task=task,
                activity_type=ClientActivity.ActivityType.NPS_SENT,
                content=f"NPS-Umfrage an {recipient_email} gesendet.",
                author=request.user,
            )

            task_completed = False
            if task.status not in (Task.Status.COMPLETED, Task.Status.SKIPPED):
                task.status = Task.Status.COMPLETED
                task.completed_at = timezone.now()
                task.completed_by = request.user
                task.save(update_fields=["status", "completed_at", "completed_by", "updated_at"])
                ClientActivity.objects.create(
                    tenant=request.tenant,
                    client=client,
                    task=task,
                    activity_type=ClientActivity.ActivityType.TASK_COMPLETED,
                    content=f'Aufgabe "{task.title}" automatisch erledigt (NPS-Umfrage gesendet).',
                    author=request.user,
                )
                task_completed = True

            return Response({"detail": "NPS-Umfrage wurde gesendet.", "task_completed": task_completed})

        context = _build_client_context(client, request.tenant)

        try:
            EmailService.send(
                tenant=request.tenant,
                template_slug=template_slug,
                recipient_email=recipient_email,
                context=context,
            )
        except Exception as e:
            return Response(
                {"detail": f"E-Mail konnte nicht gesendet werden: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Timeline-Eintrag
        ClientActivity.objects.create(
            tenant=request.tenant,
            client=client,
            task=task,
            activity_type=ClientActivity.ActivityType.EMAIL_SENT,
            content=f'E-Mail "{template_slug}" an {recipient_email} gesendet.',
            author=request.user,
        )

        # Auto-Complete: Task als erledigt markieren
        task_completed = False
        if task.status not in (Task.Status.COMPLETED, Task.Status.SKIPPED):
            task.status = Task.Status.COMPLETED
            task.completed_at = timezone.now()
            task.completed_by = request.user
            task.save(update_fields=["status", "completed_at", "completed_by", "updated_at"])
            ClientActivity.objects.create(
                tenant=request.tenant,
                client=client,
                task=task,
                activity_type=ClientActivity.ActivityType.TASK_COMPLETED,
                content=f'Aufgabe "{task.title}" automatisch erledigt (E-Mail gesendet).',
                author=request.user,
            )
            task_completed = True

        return Response({"detail": "E-Mail wurde gesendet.", "task_completed": task_completed})


# ---------------------------------------------------------------------------
# E-Mail-Sequenz aus Task heraus starten
# ---------------------------------------------------------------------------
class TaskStartSequenceView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def post(self, request, slug, pk):
        # Provider-Check
        if not EmailProviderConnection.objects.filter(tenant=request.tenant, is_active=True).exists():
            return Response(
                {"detail": "Kein E-Mail-Provider konfiguriert. Bitte richte SMTP oder SendGrid unter Integrationen → E-Mail ein."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        client = _get_client(request, slug)
        if client is None:
            return _not_found()
        try:
            task = Task.objects.select_related("email_sequence").get(
                client=client, pk=pk,
            )
        except Task.DoesNotExist:
            return _not_found("Aufgabe")

        if not task.email_sequence:
            return Response(
                {"detail": "Keine E-Mail-Sequenz mit dieser Aufgabe verknuepft."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipient_email = client.contact_email
        if not recipient_email:
            return Response(
                {"detail": "Mandant hat keine E-Mail-Adresse hinterlegt."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        context = _build_client_context(client, request.tenant)

        try:
            enrollment = EmailService.start_sequence(
                tenant=request.tenant,
                sequence_slug=task.email_sequence.slug,
                recipient_email=recipient_email,
                context=context,
            )
        except Exception as e:
            return Response(
                {"detail": f"E-Mail-Sequenz konnte nicht gestartet werden: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Timeline-Eintrag
        ClientActivity.objects.create(
            tenant=request.tenant,
            client=client,
            task=task,
            activity_type=ClientActivity.ActivityType.EMAIL_SENT,
            content=f'E-Mail-Sequenz "{task.email_sequence.name}" fuer {recipient_email} gestartet.',
            author=request.user,
        )

        # Auto-Complete
        task_completed = False
        if task.status not in (Task.Status.COMPLETED, Task.Status.SKIPPED):
            task.status = Task.Status.COMPLETED
            task.completed_at = timezone.now()
            task.completed_by = request.user
            task.save(update_fields=["status", "completed_at", "completed_by", "updated_at"])
            ClientActivity.objects.create(
                tenant=request.tenant,
                client=client,
                task=task,
                activity_type=ClientActivity.ActivityType.TASK_COMPLETED,
                content=f'Aufgabe "{task.title}" automatisch erledigt (E-Mail-Sequenz gestartet).',
                author=request.user,
            )
            task_completed = True

        return Response({
            "detail": "E-Mail-Sequenz wurde gestartet.",
            "enrollment_id": str(enrollment.pk),
            "enrollment_status": enrollment.status,
            "sequence_name": task.email_sequence.name,
            "recipient_email": recipient_email,
            "task_completed": task_completed,
        })


# ---------------------------------------------------------------------------
# Jira-Aktion aus Task heraus ausfuehren
# ---------------------------------------------------------------------------
class TaskExecuteJiraView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def post(self, request, slug, pk):
        client = _get_client(request, slug)
        if client is None:
            return _not_found()
        try:
            task = Task.objects.select_related(
                "client", "action_template", "action_sequence",
            ).get(client=client, pk=pk)
        except Task.DoesNotExist:
            return _not_found("Aufgabe")

        context = _build_client_context(client, request.tenant)

        try:
            if task.action_sequence:
                execution = IntegrationService.start_sequence(
                    tenant=request.tenant,
                    sequence_slug=task.action_sequence.slug,
                    context=context,
                    user=request.user,
                    entity_type="client",
                    entity_id=str(client.pk),
                )
            elif task.action_template:
                execution = IntegrationService.execute(
                    tenant=request.tenant,
                    template_slug=task.action_template.slug,
                    context=context,
                    user=request.user,
                    entity_type="client",
                    entity_id=str(client.pk),
                )
            else:
                return Response(
                    {"detail": "Keine Jira-Aktion mit dieser Aufgabe verknuepft."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                {"detail": f"Jira-Aktion fehlgeschlagen: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Timeline-Eintrag
        action_name = (
            task.action_sequence.name if task.action_sequence
            else task.action_template.name if task.action_template
            else "Unbekannt"
        )
        ClientActivity.objects.create(
            tenant=request.tenant,
            client=client,
            task=task,
            activity_type=ClientActivity.ActivityType.JIRA_EXECUTED,
            content=f'Jira-Aktion "{action_name}" gestartet.',
            author=request.user,
        )

        return Response({
            "detail": "Jira-Aktion wurde gestartet.",
            "execution_id": str(execution.pk),
            "status": execution.status,
        })


# ---------------------------------------------------------------------------
# Webhook-Aktion aus Task heraus ausfuehren
# ---------------------------------------------------------------------------
class TaskExecuteWebhookView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def post(self, request, slug, pk):
        client = _get_client(request, slug)
        if client is None:
            return _not_found()
        try:
            task = Task.objects.select_related(
                "client", "action_template", "action_sequence",
            ).get(client=client, pk=pk)
        except Task.DoesNotExist:
            return _not_found("Aufgabe")

        context = _build_client_context(client, request.tenant)

        try:
            if task.action_sequence:
                execution = IntegrationService.start_sequence(
                    tenant=request.tenant,
                    sequence_slug=task.action_sequence.slug,
                    context=context,
                    user=request.user,
                    entity_type="client",
                    entity_id=str(client.pk),
                )
            elif task.action_template:
                execution = IntegrationService.execute(
                    tenant=request.tenant,
                    template_slug=task.action_template.slug,
                    context=context,
                    user=request.user,
                    entity_type="client",
                    entity_id=str(client.pk),
                )
            else:
                return Response(
                    {"detail": "Keine Webhook-Aktion mit dieser Aufgabe verknuepft."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                {"detail": f"Webhook-Aktion fehlgeschlagen: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Timeline-Eintrag
        action_name = (
            task.action_sequence.name if task.action_sequence
            else task.action_template.name if task.action_template
            else "Unbekannt"
        )
        ClientActivity.objects.create(
            tenant=request.tenant,
            client=client,
            task=task,
            activity_type=ClientActivity.ActivityType.WEBHOOK_EXECUTED,
            content=f'Webhook "{action_name}" gestartet.',
            author=request.user,
        )

        return Response({
            "detail": "Webhook-Aktion wurde gestartet.",
            "execution_id": str(execution.pk),
            "status": execution.status,
        })


# ---------------------------------------------------------------------------
# Remove a loaded task list from a client
# ---------------------------------------------------------------------------
class ClientRemoveListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def post(self, request, slug):
        from apps.tasks.serializers import RemoveListSerializer

        client = _get_client(request, slug)
        if client is None:
            return _not_found()

        serializer = RemoveListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            task_list = TaskList.objects.get(pk=serializer.validated_data["task_list_id"])
        except TaskList.DoesNotExist:
            return _not_found("Aufgabenliste")

        result = TaskService.remove_list_from_client(
            tenant=request.tenant,
            client=client,
            task_list=task_list,
            author=request.user,
        )

        return Response({
            "detail": f'Aufgabenliste "{result["list_name"]}" entfernt.',
            "deleted_count": result["deleted_count"],
        })


# ---------------------------------------------------------------------------
# TaskList: Duplicate, Reorder, Usage
# ---------------------------------------------------------------------------
class TaskListDuplicateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def post(self, request, pk):
        try:
            source = TaskList.objects.prefetch_related("items__task_template").get(
                Q(tenant=request.tenant) | Q(tenant__isnull=True),
                pk=pk,
            )
        except TaskList.DoesNotExist:
            return _not_found("Aufgabenliste")

        new_list = TaskList(
            tenant=request.tenant,
            name=f"{source.name} (Kopie)",
            description=source.description,
        )
        new_list.save()

        for item in source.items.order_by("group_position", "position"):
            TaskListItem.objects.create(
                task_list=new_list,
                task_template=item.task_template,
                position=item.position,
                group_label=item.group_label,
                group_position=item.group_position,
                day_offset=item.day_offset,
            )

        return Response(
            TaskListSerializer(new_list).data,
            status=status.HTTP_201_CREATED,
        )


class TaskListReorderView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def patch(self, request, pk):
        try:
            task_list = TaskList.objects.get(
                Q(tenant=request.tenant) | Q(tenant__isnull=True),
                pk=pk,
            )
        except TaskList.DoesNotExist:
            return _not_found("Aufgabenliste")

        if task_list.tenant is None:
            return Response(
                {"detail": "System-Listen koennen nicht umsortiert werden."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TaskListReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item_ids = serializer.validated_data["item_ids"]

        items = {str(item.pk): item for item in task_list.items.all()}
        for i, item_id in enumerate(item_ids):
            item = items.get(str(item_id))
            if item:
                item.position = i
                item.save(update_fields=["position", "updated_at"])

        task_list.refresh_from_db()
        return Response(TaskListSerializer(task_list).data)


class TaskListUsageView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request, pk):
        try:
            TaskList.objects.get(
                Q(tenant=request.tenant) | Q(tenant__isnull=True),
                pk=pk,
            )
        except TaskList.DoesNotExist:
            return _not_found("Aufgabenliste")

        clients = (
            Client.objects.filter(
                tenant=request.tenant,
                tasks__source_list_id=pk,
            )
            .distinct()
            .values("slug", "name")
        )
        return Response(list(clients))


# ---------------------------------------------------------------------------
# ClientActivity views — /api/v1/clients/<slug>/activities/
# ---------------------------------------------------------------------------
class ClientActivityListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]

    def get(self, request, slug):
        client = _get_client(request, slug)
        if client is None:
            return _not_found()

        qs = ClientActivity.objects.filter(client=client).select_related("author", "task")

        # Optional: nach Typ filtern
        activity_type = request.query_params.get("type")
        if activity_type:
            qs = qs.filter(activity_type=activity_type)

        # Pagination: wenn ?page= angegeben, paginiert zurückgeben
        if "page" in request.query_params:
            paginator = PageNumberPagination()
            paginator.page_size = 50
            page = paginator.paginate_queryset(qs, request)
            serializer = ClientActivitySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ClientActivitySerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request, slug):
        """Neuen Kommentar erstellen."""
        client = _get_client(request, slug)
        if client is None:
            return _not_found()

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        task_id = data.get("task")
        task = None
        if task_id:
            try:
                task = Task.objects.get(client=client, pk=task_id)
            except Task.DoesNotExist:
                return _not_found("Aufgabe")

        activity = ClientActivity.objects.create(
            tenant=request.tenant,
            client=client,
            task=task,
            activity_type=ClientActivity.ActivityType.COMMENT,
            content=data["content"],
            author=request.user,
        )

        return Response(
            ClientActivitySerializer(activity).data,
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Recurring Task Schedules
# ---------------------------------------------------------------------------
class RecurringScheduleListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def get(self, request):
        qs = RecurringTaskSchedule.objects.filter(
            tenant=request.tenant,
        ).select_related("task_list").prefetch_related("runs")
        return Response(RecurringTaskScheduleSerializer(qs, many=True).data)

    def post(self, request):
        serializer = RecurringTaskScheduleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            task_list = TaskList.objects.get(
                Q(tenant=request.tenant) | Q(tenant__isnull=True),
                pk=data["task_list_id"],
            )
        except TaskList.DoesNotExist:
            return Response(
                {"detail": "Aufgabenliste nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if RecurringTaskSchedule.objects.filter(tenant=request.tenant, task_list=task_list).exists():
            return Response(
                {"detail": "Fuer diese Aufgabenliste existiert bereits ein Zeitplan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule = RecurringTaskSchedule.objects.create(
            tenant=request.tenant,
            task_list=task_list,
            name=data.get("name", ""),
            frequency=data["frequency"],
            is_active=data.get("is_active", True),
            client_scope=data.get("client_scope", "all_active"),
            next_run_at=TaskService.compute_next_run(data["frequency"]),
        )

        # M2M relations
        if data.get("service_type_ids"):
            schedule.service_types.set(data["service_type_ids"])
        if data.get("client_ids"):
            schedule.clients.set(data["client_ids"])

        return Response(
            RecurringTaskScheduleSerializer(schedule).data,
            status=status.HTTP_201_CREATED,
        )


class RecurringScheduleDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def _get_schedule(self, request, pk):
        try:
            return RecurringTaskSchedule.objects.select_related("task_list").get(
                tenant=request.tenant, pk=pk,
            )
        except RecurringTaskSchedule.DoesNotExist:
            return None

    def get(self, request, pk):
        schedule = self._get_schedule(request, pk)
        if schedule is None:
            return _not_found("Zeitplan")
        return Response(RecurringTaskScheduleSerializer(schedule).data)

    def patch(self, request, pk):
        schedule = self._get_schedule(request, pk)
        if schedule is None:
            return _not_found("Zeitplan")

        data = request.data
        if "name" in data:
            schedule.name = data["name"]
        if "frequency" in data:
            schedule.frequency = data["frequency"]
            # Recompute next_run_at when frequency changes
            schedule.next_run_at = TaskService.compute_next_run(data["frequency"])
        if "is_active" in data:
            schedule.is_active = data["is_active"]
        if "client_scope" in data:
            schedule.client_scope = data["client_scope"]

        schedule.save()

        if "service_type_ids" in data:
            schedule.service_types.set(data["service_type_ids"])
        if "client_ids" in data:
            schedule.clients.set(data["client_ids"])

        return Response(RecurringTaskScheduleSerializer(schedule).data)

    def delete(self, request, pk):
        schedule = self._get_schedule(request, pk)
        if schedule is None:
            return _not_found("Zeitplan")
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecurringScheduleRunsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def get(self, request, pk):
        try:
            schedule = RecurringTaskSchedule.objects.get(
                tenant=request.tenant, pk=pk,
            )
        except RecurringTaskSchedule.DoesNotExist:
            return _not_found("Zeitplan")

        runs = schedule.runs.order_by("-started_at")[:50]
        return Response(RecurringTaskRunSerializer(runs, many=True).data)


class RecurringScheduleTriggerView(APIView):
    """Manually trigger a schedule for testing purposes."""

    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def post(self, request, pk):
        try:
            schedule = RecurringTaskSchedule.objects.select_related("task_list", "tenant").get(
                tenant=request.tenant, pk=pk,
            )
        except RecurringTaskSchedule.DoesNotExist:
            return _not_found("Zeitplan")

        from apps.tasks.tasks import _execute_schedule

        _execute_schedule(schedule, timezone.now(), TaskService)

        # Return the latest run
        latest_run = schedule.runs.order_by("-started_at").first()
        if latest_run:
            return Response(RecurringTaskRunSerializer(latest_run).data)
        return Response({"detail": "Ausfuehrung gestartet."}, status=status.HTTP_200_OK)
