"""Views for the integrations API (Jira, Twilio, etc.)."""

import requests
import structlog
from django.db import models
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import Client, ClientKeyFact
from apps.common.permissions import HasActiveSubscription, IsTenantAdmin, IsTenantMember, IsTenantOwner
from apps.integrations.models import (
    ActionExecution,
    ActionSequence,
    ActionTemplate,
    ClientIntegrationData,
    ExecutionStatus,
    JiraConnection,
    SequenceStep,
    TenantIntegration,
    TwilioConnection,
)
from apps.integrations.registry import INTEGRATION_TYPES
from apps.integrations.serializers import (
    ActionExecutionListSerializer,
    ActionExecutionSerializer,
    ActionSequenceCreateSerializer,
    ActionSequenceSerializer,
    ActionTemplateCreateSerializer,
    ActionTemplateSerializer,
    ClientIntegrationDataSerializer,
    ClientIntegrationDataWriteSerializer,
    CopyConfigRequestSerializer,
    CopyConfigResultSerializer,
    CopySourceTenantSerializer,
    CreateJiraProjectSerializer,
    ExecuteActionSerializer,
    ExecuteSequenceSerializer,
    IntegrationTypeSerializer,
    JiraConnectionSerializer,
    JiraConnectionWriteSerializer,
    SequenceStepSerializer,
    SequenceStepWriteSerializer,
    TenantIntegrationToggleSerializer,
    TwilioConnectionSerializer,
    TwilioConnectionWriteSerializer,
)
from apps.integrations.config_copy_service import ConfigCopyService
from apps.integrations.services import IntegrationService
from apps.tenants.models import Tenant
from apps.users.models import Membership

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Connection (Owner only)
# ---------------------------------------------------------------------------
class JiraConnectionView(APIView):
    """GET/PUT/DELETE the tenant's Jira connection."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def get(self, request):
        conn = JiraConnection.objects.filter(tenant=request.tenant, is_active=True).first()
        if not conn:
            return Response({"detail": "Keine Jira-Verbindung konfiguriert."}, status=status.HTTP_404_NOT_FOUND)
        return Response(JiraConnectionSerializer(conn).data)

    def put(self, request):
        serializer = JiraConnectionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        defaults = {
            "label": data.get("label", "Jira Cloud"),
            "jira_url": data["jira_url"],
            "jira_email": data["jira_email"],
        }
        if "config" in request.data:
            defaults["config"] = data.get("config", {})

        conn, created = JiraConnection.objects.update_or_create(
            tenant=request.tenant,
            is_active=True,
            defaults=defaults,
        )
        conn.set_token(data["jira_api_token"])
        conn.save(update_fields=["jira_api_token_encrypted"])

        return Response(
            JiraConnectionSerializer(conn).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        updated = JiraConnection.objects.filter(tenant=request.tenant, is_active=True).update(is_active=False)
        if not updated:
            return Response({"detail": "Keine Jira-Verbindung gefunden."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class JiraConnectionTestView(APIView):
    """POST: Test the current Jira connection."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def post(self, request):
        conn = JiraConnection.objects.filter(tenant=request.tenant, is_active=True).first()
        if not conn:
            return Response({"detail": "Keine Jira-Verbindung konfiguriert."}, status=status.HTTP_404_NOT_FOUND)

        success, message = IntegrationService.test_connection(conn)
        return Response(
            {"success": success, "message": message},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Templates (Admin)
# ---------------------------------------------------------------------------
class ActionTemplateListCreateView(APIView):
    """GET: List templates (system + tenant). POST: Create tenant template."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def get(self, request):
        templates = ActionTemplate.objects.filter(
            models.Q(tenant=request.tenant) | models.Q(tenant__isnull=True),
            is_active=True,
        ).order_by("is_system", "name")

        # Optional filter by target_type (e.g. ?target_type=webhook)
        target_type = request.query_params.get("target_type")
        if target_type:
            templates = templates.filter(target_type=target_type)

        return Response(ActionTemplateSerializer(templates, many=True).data)

    def post(self, request):
        serializer = ActionTemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template = serializer.save(tenant=request.tenant)
        return Response(ActionTemplateSerializer(template).data, status=status.HTTP_201_CREATED)


class ActionTemplateDetailView(APIView):
    """GET/PATCH/DELETE a single template."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def _get_template(self, request, pk):
        return ActionTemplate.objects.filter(
            models.Q(tenant=request.tenant) | models.Q(tenant__isnull=True),
            id=pk,
        ).first()

    def get(self, request, pk):
        template = self._get_template(request, pk)
        if not template:
            return Response({"detail": "Template nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ActionTemplateSerializer(template).data)

    def patch(self, request, pk):
        template = ActionTemplate.objects.filter(tenant=request.tenant, id=pk).first()
        if not template:
            return Response({"detail": "Template nicht gefunden oder ist System-Template."}, status=status.HTTP_404_NOT_FOUND)
        if template.is_system:
            return Response({"detail": "System-Templates koennen nicht bearbeitet werden."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ActionTemplateCreateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()
        return Response(ActionTemplateSerializer(template).data)

    def delete(self, request, pk):
        template = ActionTemplate.objects.filter(tenant=request.tenant, id=pk).first()
        if not template:
            return Response({"detail": "Template nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        if template.is_system:
            return Response({"detail": "System-Templates koennen nicht geloescht werden."}, status=status.HTTP_403_FORBIDDEN)
        template.is_active = False
        template.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Sequences (Admin)
# ---------------------------------------------------------------------------
class ActionSequenceListCreateView(APIView):
    """GET: List sequences. POST: Create sequence."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def get(self, request):
        sequences = ActionSequence.objects.filter(
            models.Q(tenant=request.tenant) | models.Q(tenant__isnull=True),
            is_active=True,
        ).prefetch_related("steps__template").order_by("name")
        return Response(ActionSequenceSerializer(sequences, many=True).data)

    def post(self, request):
        serializer = ActionSequenceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sequence = serializer.save(tenant=request.tenant)
        return Response(ActionSequenceSerializer(sequence).data, status=status.HTTP_201_CREATED)


class ActionSequenceDetailView(APIView):
    """GET/PATCH/DELETE a single sequence."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def _get_sequence(self, request, pk):
        return ActionSequence.objects.filter(
            models.Q(tenant=request.tenant) | models.Q(tenant__isnull=True),
            id=pk,
        ).prefetch_related("steps__template").first()

    def get(self, request, pk):
        sequence = self._get_sequence(request, pk)
        if not sequence:
            return Response({"detail": "Sequenz nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ActionSequenceSerializer(sequence).data)

    def patch(self, request, pk):
        sequence = ActionSequence.objects.filter(tenant=request.tenant, id=pk).first()
        if not sequence:
            return Response({"detail": "Sequenz nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ActionSequenceCreateSerializer(sequence, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ActionSequenceSerializer(sequence).data)

    def delete(self, request, pk):
        sequence = ActionSequence.objects.filter(tenant=request.tenant, id=pk).first()
        if not sequence:
            return Response({"detail": "Sequenz nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        sequence.is_active = False
        sequence.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Sequence Steps
# ---------------------------------------------------------------------------
class SequenceStepListCreateView(APIView):
    """GET/POST steps within a sequence."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def _get_sequence(self, request, sequence_pk):
        return ActionSequence.objects.filter(tenant=request.tenant, id=sequence_pk).first()

    def get(self, request, sequence_pk):
        sequence = self._get_sequence(request, sequence_pk)
        if not sequence:
            return Response({"detail": "Sequenz nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        steps = sequence.steps.select_related("template").order_by("position")
        return Response(SequenceStepSerializer(steps, many=True).data)

    def post(self, request, sequence_pk):
        sequence = self._get_sequence(request, sequence_pk)
        if not sequence:
            return Response({"detail": "Sequenz nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        serializer = SequenceStepWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        step = serializer.save(sequence=sequence)
        return Response(SequenceStepSerializer(step).data, status=status.HTTP_201_CREATED)


class SequenceStepDetailView(APIView):
    """PATCH/DELETE a single step."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def _get_step(self, request, sequence_pk, pk):
        return SequenceStep.objects.filter(
            sequence__tenant=request.tenant,
            sequence_id=sequence_pk,
            id=pk,
        ).first()

    def patch(self, request, sequence_pk, pk):
        step = self._get_step(request, sequence_pk, pk)
        if not step:
            return Response({"detail": "Step nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        serializer = SequenceStepWriteSerializer(step, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SequenceStepSerializer(step).data)

    def delete(self, request, sequence_pk, pk):
        step = self._get_step(request, sequence_pk, pk)
        if not step:
            return Response({"detail": "Step nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        step.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------
class ExecuteActionView(APIView):
    """POST: Execute a single template."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def post(self, request):
        serializer = ExecuteActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            execution = IntegrationService.execute(
                tenant=request.tenant,
                template_slug=data["template_slug"],
                context=data.get("context", {}),
                user=request.user,
                entity_type=data.get("entity_type", ""),
                entity_id=data.get("entity_id", ""),
                idempotency_key=data.get("idempotency_key", ""),
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ActionExecutionListSerializer(execution).data, status=status.HTTP_202_ACCEPTED)


class ExecuteSequenceView(APIView):
    """POST: Start a sequence execution."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def post(self, request):
        serializer = ExecuteSequenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            execution = IntegrationService.start_sequence(
                tenant=request.tenant,
                sequence_slug=data["sequence_slug"],
                context=data.get("context", {}),
                user=request.user,
                entity_type=data.get("entity_type", ""),
                entity_id=data.get("entity_id", ""),
                idempotency_key=data.get("idempotency_key", ""),
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ActionExecutionListSerializer(execution).data, status=status.HTTP_202_ACCEPTED)


class ExecutionListView(APIView):
    """GET: List executions for the tenant."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def get(self, request):
        qs = ActionExecution.objects.filter(tenant=request.tenant).select_related(
            "sequence", "template", "triggered_by"
        ).order_by("-created_at")

        # Optional filters
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        entity_type = request.query_params.get("entity_type")
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        entity_id = request.query_params.get("entity_id")
        if entity_id:
            qs = qs.filter(entity_id=entity_id)

        return Response(ActionExecutionListSerializer(qs[:100], many=True).data)


class ExecutionDetailView(APIView):
    """GET: Execution detail with step logs."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def get(self, request, pk):
        execution = (
            ActionExecution.objects.filter(tenant=request.tenant, id=pk)
            .select_related("sequence", "template", "triggered_by")
            .prefetch_related("step_logs__template")
            .first()
        )
        if not execution:
            return Response({"detail": "Ausfuehrung nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ActionExecutionSerializer(execution).data)


class ExecutionCancelView(APIView):
    """POST: Cancel a pending/running execution."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def post(self, request, pk):
        execution = ActionExecution.objects.filter(tenant=request.tenant, id=pk).first()
        if not execution:
            return Response({"detail": "Ausfuehrung nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        execution = IntegrationService.cancel_execution(execution)
        return Response(ActionExecutionListSerializer(execution).data)


# ---------------------------------------------------------------------------
# Jira Proxy (read-only Jira API calls for the frontend)
# ---------------------------------------------------------------------------
class JiraProjectsView(APIView):
    """GET: List Jira projects."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def get(self, request):
        conn = JiraConnection.objects.filter(tenant=request.tenant, is_active=True).first()
        if not conn:
            return Response({"detail": "Keine Jira-Verbindung."}, status=status.HTTP_404_NOT_FOUND)

        try:
            token = conn.get_token()
            resp = requests.get(
                f"{conn.jira_url}/rest/api/3/project",
                auth=(conn.jira_email, token),
                headers={"Accept": "application/json"},
                timeout=10,
            )
            if resp.status_code == 200:
                return Response(resp.json())
            return Response({"detail": f"Jira API Fehler: {resp.status_code}"}, status=resp.status_code)
        except requests.RequestException as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class JiraIssueTypesView(APIView):
    """GET: List issue types for a project."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def get(self, request, project_key):
        conn = JiraConnection.objects.filter(tenant=request.tenant, is_active=True).first()
        if not conn:
            return Response({"detail": "Keine Jira-Verbindung."}, status=status.HTTP_404_NOT_FOUND)

        try:
            token = conn.get_token()
            resp = requests.get(
                f"{conn.jira_url}/rest/api/3/project/{project_key}",
                auth=(conn.jira_email, token),
                headers={"Accept": "application/json"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return Response(data.get("issueTypes", []))
            return Response({"detail": f"Jira API Fehler: {resp.status_code}"}, status=resp.status_code)
        except requests.RequestException as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class JiraFieldsView(APIView):
    """GET: List available Jira fields."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def get(self, request):
        conn = JiraConnection.objects.filter(tenant=request.tenant, is_active=True).first()
        if not conn:
            return Response({"detail": "Keine Jira-Verbindung."}, status=status.HTTP_404_NOT_FOUND)

        try:
            token = conn.get_token()
            resp = requests.get(
                f"{conn.jira_url}/rest/api/3/field",
                auth=(conn.jira_email, token),
                headers={"Accept": "application/json"},
                timeout=10,
            )
            if resp.status_code == 200:
                return Response(resp.json())
            return Response({"detail": f"Jira API Fehler: {resp.status_code}"}, status=resp.status_code)
        except requests.RequestException as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


# ---------------------------------------------------------------------------
# Integration Types (Registry-based)
# ---------------------------------------------------------------------------
class IntegrationTypeListView(APIView):
    """GET: List all integration types with their field definitions + enabled status."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]

    def get(self, request):
        enabled_types = set(
            TenantIntegration.objects.filter(
                tenant=request.tenant, is_enabled=True
            ).values_list("integration_type", flat=True)
        )

        result = []
        for typedef in INTEGRATION_TYPES.values():
            result.append({
                "key": typedef.key,
                "label": typedef.label,
                "description": typedef.description,
                "icon": typedef.icon,
                "fields": [
                    {"key": f.key, "label": f.label, "field_type": f.field_type}
                    for f in typedef.fields
                ],
                "is_enabled": typedef.key in enabled_types,
            })

        return Response(IntegrationTypeSerializer(result, many=True).data)


class IntegrationToggleView(APIView):
    """POST: Enable/disable an integration type for the tenant."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def post(self, request):
        serializer = TenantIntegrationToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        TenantIntegration.objects.update_or_create(
            tenant=request.tenant,
            integration_type=data["integration_type"],
            defaults={
                "is_enabled": data["is_enabled"],
                "enabled_by": request.user,
            },
        )

        return Response({"integration_type": data["integration_type"], "is_enabled": data["is_enabled"]})


# ---------------------------------------------------------------------------
# Config Copy
# ---------------------------------------------------------------------------
class CopyConfigSourcesView(APIView):
    """GET: List tenants the user owns that have copyable configurations."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def get(self, request):
        sources = ConfigCopyService.get_copyable_sources(
            user=request.user,
            exclude_tenant=request.tenant,
        )
        return Response(CopySourceTenantSerializer(sources, many=True).data)


class CopyConfigView(APIView):
    """POST: Copy integration configs from another tenant."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def post(self, request):
        serializer = CopyConfigRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        source_tenant = Tenant.objects.filter(id=data["source_tenant_id"], is_active=True).first()
        if not source_tenant:
            return Response(
                {"detail": "Quell-Mandant nicht gefunden oder inaktiv."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # User must also be owner of the source tenant
        is_source_owner = Membership.objects.filter(
            user=request.user,
            tenant=source_tenant,
            role="owner",
            is_active=True,
        ).exists()
        if not is_source_owner:
            return Response(
                {"detail": "Sie muessen Owner des Quell-Mandanten sein."},
                status=status.HTTP_403_FORBIDDEN,
            )

        result = ConfigCopyService.copy_config(
            source_tenant=source_tenant,
            target_tenant=request.tenant,
            types=data["types"],
            overwrite=data["overwrite"],
            user=request.user,
            request=request,
        )
        return Response(CopyConfigResultSerializer(result).data)


# ---------------------------------------------------------------------------
# Client Integration Data
# ---------------------------------------------------------------------------
class ClientIntegrationDataListView(APIView):
    """
    GET: List integration data for a client (only enabled integrations).
    PUT: Create/update integration data for a client.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def _get_client(self, request, slug):
        return Client.objects.filter(tenant=request.tenant, slug=slug).first()

    def get(self, request, slug):
        client = self._get_client(request, slug)
        if not client:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        enabled_types = set(
            TenantIntegration.objects.filter(
                tenant=request.tenant, is_enabled=True
            ).values_list("integration_type", flat=True)
        )

        data = ClientIntegrationData.objects.filter(
            client=client, integration_type__in=enabled_types
        )
        return Response(ClientIntegrationDataSerializer(data, many=True).data)

    def put(self, request, slug):
        client = self._get_client(request, slug)
        if not client:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ClientIntegrationDataWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Pruefen ob Integration aktiviert ist
        is_enabled = TenantIntegration.objects.filter(
            tenant=request.tenant,
            integration_type=data["integration_type"],
            is_enabled=True,
        ).exists()

        if not is_enabled:
            return Response(
                {"detail": f"Integration '{data['integration_type']}' ist nicht aktiviert."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj, created = ClientIntegrationData.objects.update_or_create(
            client=client,
            integration_type=data["integration_type"],
            defaults={"data": data["data"], "tenant": request.tenant},
        )

        return Response(
            ClientIntegrationDataSerializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Create Jira Project (synchronous, dedicated endpoint)
# ---------------------------------------------------------------------------
class CreateJiraProjectView(APIView):
    """POST: Create a Jira project for a client and store the result."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def post(self, request, slug):
        serializer = CreateJiraProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Load client
        client = Client.objects.filter(tenant=request.tenant, slug=slug).first()
        if not client:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        # Check Jira integration is enabled
        is_enabled = TenantIntegration.objects.filter(
            tenant=request.tenant, integration_type="jira", is_enabled=True
        ).exists()
        if not is_enabled:
            return Response(
                {"detail": "Jira-Integration ist nicht aktiviert."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check no project is already linked
        existing = ClientIntegrationData.objects.filter(
            client=client, integration_type="jira"
        ).first()
        if existing and (existing.data.get("project_key") or existing.data.get("project_id")):
            return Response(
                {"detail": "Für diesen Mandanten ist bereits ein Jira-Projekt verknüpft."},
                status=status.HTTP_409_CONFLICT,
            )

        # Load active Jira connection
        conn = JiraConnection.objects.filter(tenant=request.tenant, is_active=True).first()
        if not conn:
            return Response(
                {"detail": "Keine aktive Jira-Verbindung konfiguriert."},
                status=status.HTTP_404_NOT_FOUND,
            )

        token = conn.get_token()
        auth = (conn.jira_email, token)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # Step 1: Get current user's accountId as project lead
        try:
            myself_resp = requests.get(
                f"{conn.jira_url}/rest/api/3/myself",
                auth=auth,
                headers=headers,
                timeout=10,
            )
            if myself_resp.status_code != 200:
                return Response(
                    {"detail": f"Jira /myself fehlgeschlagen: {myself_resp.status_code}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            lead_account_id = myself_resp.json().get("accountId")
        except requests.RequestException as e:
            return Response({"detail": f"Jira-Verbindungsfehler: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

        # Step 2: Create the project
        try:
            create_resp = requests.post(
                f"{conn.jira_url}/rest/api/3/project",
                auth=auth,
                headers=headers,
                json={
                    "key": data["project_key"],
                    "name": data["project_name"],
                    "projectTypeKey": "business",
                    "leadAccountId": lead_account_id,
                },
                timeout=15,
            )
            if create_resp.status_code not in (200, 201):
                body = create_resp.json() if create_resp.headers.get("content-type", "").startswith("application/json") else {}
                detail = body.get("errors", body.get("errorMessages", [f"HTTP {create_resp.status_code}"]))
                return Response({"detail": f"Jira-Projekt konnte nicht erstellt werden: {detail}"}, status=status.HTTP_502_BAD_GATEWAY)
            project_data = create_resp.json()
        except requests.RequestException as e:
            return Response({"detail": f"Jira-Verbindungsfehler: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

        # Step 3: Save to ClientIntegrationData
        project_id = str(project_data.get("id", ""))
        project_key = project_data.get("key", data["project_key"])
        project_url = f"{conn.jira_url}/browse/{project_key}"

        integration_data = {
            "project_url": project_url,
            "project_key": project_key,
            "project_id": project_id,
        }

        obj, _ = ClientIntegrationData.objects.update_or_create(
            client=client,
            integration_type="jira",
            defaults={"data": integration_data, "tenant": request.tenant},
        )

        return Response(ClientIntegrationDataSerializer(obj).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Twilio — Connection, Test, Token, TwiML Webhook
# ---------------------------------------------------------------------------
class TwilioConnectionView(APIView):
    """GET/PUT/DELETE the tenant's Twilio connection."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def get(self, request):
        conn = TwilioConnection.objects.filter(tenant=request.tenant, is_active=True).first()
        if not conn:
            return Response({"detail": "Keine Twilio-Verbindung konfiguriert."}, status=status.HTTP_404_NOT_FOUND)
        return Response(TwilioConnectionSerializer(conn).data)

    def put(self, request):
        serializer = TwilioConnectionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        conn, created = TwilioConnection.objects.update_or_create(
            tenant=request.tenant,
            is_active=True,
            defaults={
                "label": data.get("label", "Twilio Telefonie"),
                "account_sid": data["account_sid"],
                "twiml_app_sid": data["twiml_app_sid"],
                "phone_number": data["phone_number"],
            },
        )
        conn.set_auth_token(data["auth_token"])
        conn.save(update_fields=["auth_token_encrypted"])

        return Response(
            TwilioConnectionSerializer(conn).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        updated = TwilioConnection.objects.filter(tenant=request.tenant, is_active=True).update(is_active=False)
        if not updated:
            return Response({"detail": "Keine Twilio-Verbindung gefunden."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TwilioConnectionTestView(APIView):
    """POST: Test the current Twilio connection by fetching the account info."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def post(self, request):
        conn = TwilioConnection.objects.filter(tenant=request.tenant, is_active=True).first()
        if not conn:
            return Response({"detail": "Keine Twilio-Verbindung konfiguriert."}, status=status.HTTP_404_NOT_FOUND)

        try:
            from twilio.rest import Client as TwilioClient

            client = TwilioClient(conn.account_sid, conn.get_auth_token())
            account = client.api.accounts(conn.account_sid).fetch()
            success = account.status == "active"
            message = f"Verbindung erfolgreich. Account-Status: {account.status}" if success else f"Account ist nicht aktiv (Status: {account.status})."
        except Exception as e:
            success = False
            message = f"Verbindungstest fehlgeschlagen: {e}"

        conn.last_tested_at = timezone.now()
        conn.last_test_success = success
        conn.save(update_fields=["last_tested_at", "last_test_success"])

        return Response({"success": success, "message": message})


class TwilioAccessTokenView(APIView):
    """POST: Generate a short-lived Twilio Access Token for the Voice SDK."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]

    def post(self, request):
        conn = TwilioConnection.objects.filter(tenant=request.tenant, is_active=True).first()
        if not conn:
            return Response({"detail": "Keine Twilio-Verbindung konfiguriert."}, status=status.HTTP_404_NOT_FOUND)

        try:
            from twilio.jwt.access_token import AccessToken
            from twilio.jwt.access_token.grants import VoiceGrant

            token = AccessToken(
                conn.account_sid,
                conn.twiml_app_sid,
                conn.get_auth_token(),
                identity=request.user.email,
                ttl=3600,
            )
            voice_grant = VoiceGrant(
                outgoing_application_sid=conn.twiml_app_sid,
                incoming_allow=False,
            )
            token.add_grant(voice_grant)

            return Response({
                "token": token.to_jwt(),
                "identity": request.user.email,
                "phone_number": conn.phone_number,
            })
        except Exception as e:
            logger.error("twilio_token_generation_failed", error=str(e))
            return Response(
                {"detail": f"Token-Generierung fehlgeschlagen: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class TwiMLVoiceView(APIView):
    """POST: TwiML webhook that Twilio calls to get dial instructions.

    This is a public endpoint — Twilio calls it without JWT auth.
    Returns TwiML XML that tells Twilio to dial the target number.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        to = request.data.get("To") or request.POST.get("To", "")
        caller_id = request.data.get("CallerId") or request.POST.get("CallerId", "")

        if not to:
            twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Say language="de-DE">Keine Zielnummer angegeben.</Say></Response>'
            return HttpResponse(twiml, content_type="application/xml")

        twiml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f'<Dial callerId="{caller_id}">'
            f"<Number>{to}</Number>"
            "</Dial>"
            "</Response>"
        )
        return HttpResponse(twiml, content_type="application/xml")


# ---------------------------------------------------------------------------
# Confluence — Sync Key-Facts + Spaces Proxy
# ---------------------------------------------------------------------------
def _build_confluence_page_body(client, key_facts):
    """Build XHTML body (Confluence storage format) with client info + key facts table."""
    from xml.sax.saxutils import escape

    rows = ""
    for kf in key_facts:
        rows += (
            "<tr>"
            f"<td><strong>{escape(kf.label)}</strong></td>"
            f"<td>{escape(kf.value)}</td>"
            "</tr>"
        )

    if not rows:
        rows = '<tr><td colspan="2"><em>Keine Key-Facts vorhanden.</em></td></tr>'

    body = (
        f"<h2>Mandant: {escape(client.name)}</h2>"
        "<table>"
        "<thead><tr><th>Eigenschaft</th><th>Wert</th></tr></thead>"
        "<tbody>"
        f'<tr><td><strong>Kontakt</strong></td><td>{escape(client.contact_first_name)} {escape(client.contact_last_name)}</td></tr>'
        f'<tr><td><strong>E-Mail</strong></td><td>{escape(client.contact_email)}</td></tr>'
        f'<tr><td><strong>Telefon</strong></td><td>{escape(client.contact_phone)}</td></tr>'
        f'<tr><td><strong>Website</strong></td><td>{escape(client.website)}</td></tr>'
        f'<tr><td><strong>Status</strong></td><td>{escape(client.status)}</td></tr>'
        f'<tr><td><strong>Tier</strong></td><td>{escape(client.tier)}</td></tr>'
        "</tbody>"
        "</table>"
        "<h3>Key-Facts</h3>"
        "<table>"
        "<thead><tr><th>Label</th><th>Wert</th></tr></thead>"
        "<tbody>"
        f"{rows}"
        "</tbody>"
        "</table>"
    )
    return body


class SyncConfluencePageView(APIView):
    """POST: Create or update a Confluence page with client key facts."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def post(self, request, slug):
        # Load client
        client = Client.objects.filter(tenant=request.tenant, slug=slug).first()
        if not client:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        # Check Confluence integration enabled
        is_enabled = TenantIntegration.objects.filter(
            tenant=request.tenant, integration_type="confluence", is_enabled=True
        ).exists()
        if not is_enabled:
            return Response(
                {"detail": "Confluence-Integration ist nicht aktiviert."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Load Jira connection (same Atlassian credentials)
        conn = JiraConnection.objects.filter(tenant=request.tenant, is_active=True).first()
        if not conn:
            return Response(
                {"detail": "Keine aktive Jira-Verbindung konfiguriert (Atlassian-Credentials benötigt)."},
                status=status.HTTP_404_NOT_FOUND,
            )

        token = conn.get_token()
        auth = (conn.jira_email, token)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # Determine space key: from request body, then from Confluence data, then from Jira project key
        space_key = request.data.get("space_key", "").strip()
        confluence_data = {}
        existing = ClientIntegrationData.objects.filter(client=client, integration_type="confluence").first()
        if existing:
            confluence_data = existing.data or {}

        if not space_key:
            space_key = confluence_data.get("space_key", "")
        if not space_key:
            jira_data = ClientIntegrationData.objects.filter(client=client, integration_type="jira").first()
            if jira_data:
                space_key = (jira_data.data or {}).get("project_key", "")

        if not space_key:
            return Response(
                {"detail": "Kein Space-Key angegeben und kein Jira-Projekt verknüpft."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Collect key facts
        key_facts = list(ClientKeyFact.objects.filter(client=client).order_by("position", "created_at"))

        # Build page content
        page_title = f"Aftersales – {client.name}"
        page_body = _build_confluence_page_body(client, key_facts)

        page_id = confluence_data.get("page_id", "")

        try:
            if page_id:
                # UPDATE existing page: get current version first
                version_resp = requests.get(
                    f"{conn.jira_url}/wiki/api/v2/pages/{page_id}",
                    auth=auth,
                    headers=headers,
                    timeout=10,
                )
                if version_resp.status_code != 200:
                    return Response(
                        {"detail": f"Confluence-Seite konnte nicht geladen werden: {version_resp.status_code}"},
                        status=status.HTTP_502_BAD_GATEWAY,
                    )
                current_version = version_resp.json().get("version", {}).get("number", 1)

                update_resp = requests.put(
                    f"{conn.jira_url}/wiki/api/v2/pages/{page_id}",
                    auth=auth,
                    headers=headers,
                    json={
                        "id": page_id,
                        "status": "current",
                        "title": page_title,
                        "body": {"representation": "storage", "value": page_body},
                        "version": {"number": current_version + 1},
                    },
                    timeout=15,
                )
                if update_resp.status_code not in (200, 201):
                    body = update_resp.json() if "json" in update_resp.headers.get("content-type", "") else {}
                    return Response(
                        {"detail": f"Confluence-Update fehlgeschlagen: {body}"},
                        status=status.HTTP_502_BAD_GATEWAY,
                    )
                result_data = update_resp.json()
            else:
                # CREATE new page: first find space ID
                space_resp = requests.get(
                    f"{conn.jira_url}/wiki/api/v2/spaces?keys={space_key}",
                    auth=auth,
                    headers=headers,
                    timeout=10,
                )
                if space_resp.status_code != 200:
                    return Response(
                        {"detail": f"Confluence-Space konnte nicht geladen werden: {space_resp.status_code}"},
                        status=status.HTTP_502_BAD_GATEWAY,
                    )
                spaces = space_resp.json().get("results", [])
                if not spaces:
                    return Response(
                        {"detail": f"Confluence-Space '{space_key}' nicht gefunden."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                space_id = spaces[0]["id"]

                create_resp = requests.post(
                    f"{conn.jira_url}/wiki/api/v2/pages",
                    auth=auth,
                    headers=headers,
                    json={
                        "spaceId": space_id,
                        "status": "current",
                        "title": page_title,
                        "body": {"representation": "storage", "value": page_body},
                    },
                    timeout=15,
                )
                if create_resp.status_code not in (200, 201):
                    body = create_resp.json() if "json" in create_resp.headers.get("content-type", "") else {}
                    return Response(
                        {"detail": f"Confluence-Seite konnte nicht erstellt werden: {body}"},
                        status=status.HTTP_502_BAD_GATEWAY,
                    )
                result_data = create_resp.json()

        except requests.RequestException as e:
            return Response({"detail": f"Confluence-Verbindungsfehler: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

        # Save result in ClientIntegrationData
        new_page_id = str(result_data.get("id", ""))
        page_url = f"{conn.jira_url}/wiki/spaces/{space_key}/pages/{new_page_id}"
        # Try to get a nicer URL from the response
        links = result_data.get("_links", {})
        if links.get("webui"):
            page_url = f"{conn.jira_url}/wiki{links['webui']}"

        integration_data = {
            "space_key": space_key,
            "page_url": page_url,
            "page_id": new_page_id,
        }

        obj, _ = ClientIntegrationData.objects.update_or_create(
            client=client,
            integration_type="confluence",
            defaults={"data": integration_data, "tenant": request.tenant},
        )

        return Response(
            ClientIntegrationDataSerializer(obj).data,
            status=status.HTTP_201_CREATED if not page_id else status.HTTP_200_OK,
        )


class ConfluenceSpacesView(APIView):
    """GET: List Confluence spaces (for dropdown selection)."""

    def get_permissions(self):
        return [IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def get(self, request):
        conn = JiraConnection.objects.filter(tenant=request.tenant, is_active=True).first()
        if not conn:
            return Response({"detail": "Keine Jira-Verbindung."}, status=status.HTTP_404_NOT_FOUND)

        try:
            token = conn.get_token()
            resp = requests.get(
                f"{conn.jira_url}/wiki/api/v2/spaces?limit=50",
                auth=(conn.jira_email, token),
                headers={"Accept": "application/json"},
                timeout=10,
            )
            if resp.status_code == 200:
                return Response(resp.json().get("results", []))
            return Response({"detail": f"Confluence API Fehler: {resp.status_code}"}, status=resp.status_code)
        except requests.RequestException as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
