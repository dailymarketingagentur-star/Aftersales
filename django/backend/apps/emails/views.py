import base64
import logging
from email.utils import parseaddr
from urllib.parse import unquote

from django.db import models as db_models
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import HasActiveSubscription, IsTenantAdmin, IsTenantMember, IsTenantOwner
from apps.emails.models import (
    EmailLog,
    EmailProviderConnection,
    EmailProviderType,
    EmailSequence,
    EmailTemplate,
    InboundEmail,
    SequenceEnrollment,
    WhatsAppMessage,
)
from apps.emails.provider_service import EmailProviderService
from apps.emails.serializers import (
    EmailLogSerializer,
    EmailProviderConnectionSerializer,
    EmailSequenceSerializer,
    EmailTemplateCreateSerializer,
    EmailTemplateSerializer,
    EmailTemplateUpdateSerializer,
    InboundEmailSerializer,
    SendEmailSerializer,
    SendGridConnectionWriteSerializer,
    SequenceEnrollmentSerializer,
    SmtpConnectionWriteSerializer,
    StartSequenceSerializer,
    WhatsAppMessageSerializer,
)
from apps.emails.services import EmailService

# 1x1 transparent PNG
TRACKING_PIXEL = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "2mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


# ------------------------------------------------------------------
# Templates CRUD
# ------------------------------------------------------------------


class EmailTemplateListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def get(self, request):
        templates = EmailTemplate.objects.filter(
            db_models.Q(tenant=request.tenant) | db_models.Q(tenant__isnull=True),
            is_active=True,
        ).order_by("-created_at")
        serializer = EmailTemplateSerializer(templates, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EmailTemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template = EmailTemplate.objects.create(
            tenant=request.tenant,
            **serializer.validated_data,
        )
        return Response(
            EmailTemplateSerializer(template).data,
            status=status.HTTP_201_CREATED,
        )


class EmailTemplateDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def get(self, request, pk):
        try:
            template = EmailTemplate.objects.get(
                db_models.Q(tenant=request.tenant) | db_models.Q(tenant__isnull=True),
                id=pk,
            )
        except EmailTemplate.DoesNotExist:
            return Response({"detail": "Template not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmailTemplateSerializer(template).data)

    def patch(self, request, pk):
        try:
            template = EmailTemplate.objects.get(id=pk, tenant=request.tenant)
        except EmailTemplate.DoesNotExist:
            return Response({"detail": "Template not found or not editable."}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmailTemplateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(template, field, value)
        template.save()
        return Response(EmailTemplateSerializer(template).data)

    def delete(self, request, pk):
        try:
            template = EmailTemplate.objects.get(id=pk, tenant=request.tenant)
        except EmailTemplate.DoesNotExist:
            return Response({"detail": "Template not found or not deletable."}, status=status.HTTP_404_NOT_FOUND)
        template.is_active = False
        template.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------
# Logs (read-only list)
# ------------------------------------------------------------------


class EmailLogListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]
    serializer_class = EmailLogSerializer

    def get_queryset(self):
        qs = EmailLog.objects.filter(tenant=self.request.tenant)
        filter_status = self.request.query_params.get("status")
        if filter_status:
            qs = qs.filter(status=filter_status)
        template_slug = self.request.query_params.get("template_slug")
        if template_slug:
            qs = qs.filter(template_slug=template_slug)
        recipient = self.request.query_params.get("recipient_email")
        if recipient:
            qs = qs.filter(recipient_email=recipient)
        return qs


# ------------------------------------------------------------------
# Send (action)
# ------------------------------------------------------------------


class SendEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def post(self, request):
        if not EmailProviderConnection.objects.filter(tenant=request.tenant, is_active=True).exists():
            return Response(
                {"detail": "Kein E-Mail-Provider konfiguriert. Bitte richte SMTP oder SendGrid unter Integrationen → E-Mail ein."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        serializer = SendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            email_log = EmailService.send(
                tenant=request.tenant,
                template_slug=data["template_slug"],
                recipient_email=data["recipient_email"],
                context=data.get("context", {}),
                idempotency_key=data.get("idempotency_key") or None,
                scheduled_at=data.get("scheduled_at"),
            )
        except EmailTemplate.DoesNotExist as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            EmailLogSerializer(email_log).data,
            status=status.HTTP_202_ACCEPTED,
        )


# ------------------------------------------------------------------
# Sequences (read-only list)
# ------------------------------------------------------------------


class EmailSequenceListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]
    serializer_class = EmailSequenceSerializer

    def get_queryset(self):
        return EmailSequence.objects.filter(
            db_models.Q(tenant=self.request.tenant) | db_models.Q(tenant__isnull=True),
            is_active=True,
        ).prefetch_related("steps__template")


# ------------------------------------------------------------------
# Sequence enrollment
# ------------------------------------------------------------------


class StartSequenceView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def post(self, request):
        serializer = StartSequenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            enrollment = EmailService.start_sequence(
                tenant=request.tenant,
                sequence_slug=data["sequence_slug"],
                recipient_email=data["recipient_email"],
                context=data.get("context", {}),
            )
        except EmailSequence.DoesNotExist as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            SequenceEnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED,
        )


class EnrollmentListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]
    serializer_class = SequenceEnrollmentSerializer

    def get_queryset(self):
        return SequenceEnrollment.objects.filter(
            tenant=self.request.tenant,
        ).select_related("sequence")


class CancelEnrollmentView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def post(self, request, pk):
        try:
            enrollment = SequenceEnrollment.objects.get(
                id=pk, tenant=request.tenant,
            )
        except SequenceEnrollment.DoesNotExist:
            return Response({"detail": "Enrollment not found."}, status=status.HTTP_404_NOT_FOUND)

        enrollment = EmailService.cancel_sequence(enrollment.id)
        return Response(SequenceEnrollmentSerializer(enrollment).data)


# ------------------------------------------------------------------
# Public tracking endpoints (no auth, no tenant header)
# ------------------------------------------------------------------


class TrackOpenView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request, tracking_id):
        EmailLog.objects.filter(
            tracking_id=tracking_id,
            opened_at__isnull=True,
        ).update(opened_at=timezone.now())
        return HttpResponse(TRACKING_PIXEL, content_type="image/png")


class TrackClickView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request, tracking_id):
        url = request.query_params.get("url", "")
        url = unquote(url)

        # Validate URL scheme — only allow http/https
        if not url.startswith(("http://", "https://")):
            return Response(
                {"detail": "Invalid redirect URL."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        EmailLog.objects.filter(
            tracking_id=tracking_id,
            clicked_at__isnull=True,
        ).update(clicked_at=timezone.now())

        return HttpResponseRedirect(url)


# ------------------------------------------------------------------
# Email Provider Connections (Owner only)
# ------------------------------------------------------------------


class EmailProviderListView(APIView):
    """GET all configured email providers for the tenant."""

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def get(self, request):
        providers = EmailProviderConnection.objects.filter(tenant=request.tenant)
        return Response(EmailProviderConnectionSerializer(providers, many=True).data)


class EmailProviderStatusView(APIView):
    """Lightweight status check: does the tenant have an active email provider?"""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request):
        conn = EmailProviderConnection.objects.filter(
            tenant=request.tenant, is_active=True,
        ).first()

        if conn is None:
            return Response({
                "has_active_provider": False,
                "provider_type": None,
                "from_email": None,
            })

        from_email = conn.from_email
        if conn.from_name:
            from_email = f"{conn.from_name} <{conn.from_email}>"

        return Response({
            "has_active_provider": True,
            "provider_type": conn.provider_type,
            "from_email": from_email,
        })


class _BaseProviderView(APIView):
    """Shared base for SMTP / SendGrid views. Subclasses set provider_type + write_serializer_class."""

    provider_type: str
    write_serializer_class = None

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def _get_conn(self, tenant):
        return EmailProviderConnection.objects.filter(
            tenant=tenant, provider_type=self.provider_type,
        ).first()

    def get(self, request):
        conn = self._get_conn(request.tenant)
        if not conn:
            return Response(
                {"detail": "Nicht konfiguriert."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(EmailProviderConnectionSerializer(conn).data)

    def put(self, request):
        serializer = self.write_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        conn = self._get_conn(request.tenant)
        created = conn is None
        if created:
            conn = EmailProviderConnection(
                tenant=request.tenant,
                provider_type=self.provider_type,
            )

        conn.label = data.get("label", conn.label)
        conn.from_email = data["from_email"]
        conn.from_name = data.get("from_name", "")
        self._apply_provider_fields(conn, data)
        conn.save()

        return Response(
            EmailProviderConnectionSerializer(conn).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def _apply_provider_fields(self, conn, data):
        raise NotImplementedError

    def delete(self, request):
        deleted, _ = EmailProviderConnection.objects.filter(
            tenant=request.tenant, provider_type=self.provider_type,
        ).delete()
        if not deleted:
            return Response(
                {"detail": "Nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SmtpProviderView(_BaseProviderView):
    provider_type = EmailProviderType.SMTP
    write_serializer_class = SmtpConnectionWriteSerializer

    def _apply_provider_fields(self, conn, data):
        conn.smtp_host = data["smtp_host"]
        conn.smtp_port = data.get("smtp_port", 587)
        conn.smtp_username = data.get("smtp_username", "")
        conn.smtp_use_tls = data.get("smtp_use_tls", True)
        if data.get("smtp_password"):
            conn.set_smtp_password(data["smtp_password"])


class SendGridProviderView(_BaseProviderView):
    provider_type = EmailProviderType.SENDGRID
    write_serializer_class = SendGridConnectionWriteSerializer

    def _apply_provider_fields(self, conn, data):
        if data.get("sendgrid_api_key"):
            conn.set_sendgrid_api_key(data["sendgrid_api_key"])
        conn.inbound_parse_enabled = data.get("inbound_parse_enabled", False)
        conn.inbound_parse_domain = data.get("inbound_parse_domain", "")


class _BaseProviderTestView(APIView):
    provider_type: str

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def post(self, request):
        conn = EmailProviderConnection.objects.filter(
            tenant=request.tenant, provider_type=self.provider_type,
        ).first()
        if not conn:
            return Response(
                {"detail": "Nicht konfiguriert."},
                status=status.HTTP_404_NOT_FOUND,
            )
        success, message = EmailProviderService.test_connection(conn)
        return Response({"success": success, "message": message})


class SmtpProviderTestView(_BaseProviderTestView):
    provider_type = EmailProviderType.SMTP


class SendGridProviderTestView(_BaseProviderTestView):
    provider_type = EmailProviderType.SENDGRID


class _BaseProviderActivateView(APIView):
    provider_type: str

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsTenantOwner(), HasActiveSubscription()]

    def post(self, request):
        conn = EmailProviderConnection.objects.filter(
            tenant=request.tenant, provider_type=self.provider_type,
        ).first()
        if not conn:
            return Response(
                {"detail": "Nicht konfiguriert."},
                status=status.HTTP_404_NOT_FOUND,
            )
        # Deactivate all other providers for this tenant
        EmailProviderConnection.objects.filter(
            tenant=request.tenant,
        ).exclude(id=conn.id).update(is_active=False)
        # Activate this one
        conn.is_active = True
        conn.save(update_fields=["is_active"])
        return Response(EmailProviderConnectionSerializer(conn).data)


class SmtpProviderActivateView(_BaseProviderActivateView):
    provider_type = EmailProviderType.SMTP


class SendGridProviderActivateView(_BaseProviderActivateView):
    provider_type = EmailProviderType.SENDGRID


# ------------------------------------------------------------------
# Inbound Parse (SendGrid webhook + authenticated inbox)
# ------------------------------------------------------------------


class SendGridInboundWebhookView(APIView):
    """Public webhook endpoint for SendGrid Inbound Parse.

    URL contains tenant UUID for routing — no auth required (like TrackOpenView).
    """

    permission_classes = []
    authentication_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, tenant_id):
        from apps.tenants.models import Tenant

        logger = logging.getLogger(__name__)

        try:
            tenant = Tenant.objects.get(id=tenant_id, is_active=True)
        except Tenant.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Check if inbound parse is enabled for this tenant
        conn = EmailProviderConnection.objects.filter(
            tenant=tenant,
            provider_type=EmailProviderType.SENDGRID,
            inbound_parse_enabled=True,
        ).first()
        if not conn:
            logger.warning("Inbound webhook called for tenant %s but inbound parse not enabled", tenant_id)
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Extract fields from SendGrid POST
        from_raw = request.data.get("from", "")
        from_name, from_email = parseaddr(from_raw)
        to_email = request.data.get("to", "")
        subject = request.data.get("subject", "")[:500]
        body_text = request.data.get("text", "")
        attachment_count = int(request.data.get("attachments", 0))

        if not from_email:
            return Response({"detail": "Missing from address."}, status=status.HTTP_400_BAD_REQUEST)

        # Client matching: try ClientEmailAddress first, then contact_email
        from apps.clients.models import Client, ClientEmailAddress

        client = None
        email_match = ClientEmailAddress.objects.filter(
            tenant=tenant, email__iexact=from_email,
        ).select_related("client").first()
        if email_match:
            client = email_match.client
        else:
            client = Client.objects.filter(tenant=tenant, contact_email__iexact=from_email).first()

        is_assigned = client is not None

        InboundEmail.objects.create(
            tenant=tenant,
            from_email=from_email,
            from_name=from_name,
            to_email=to_email,
            subject=subject,
            body_text=body_text,
            client=client,
            has_attachments=attachment_count > 0,
            is_read=False,
            is_assigned=is_assigned,
        )

        return Response(status=status.HTTP_200_OK)


class InboundEmailListView(ListAPIView):
    """Authenticated list of inbound emails for the current tenant."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]
    serializer_class = InboundEmailSerializer

    def get_queryset(self):
        qs = InboundEmail.objects.filter(tenant=self.request.tenant).select_related("client")
        assigned = self.request.query_params.get("assigned")
        if assigned == "true":
            qs = qs.filter(is_assigned=True)
        elif assigned == "false":
            qs = qs.filter(is_assigned=False)
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs


class InboundEmailDetailView(APIView):
    """GET single inbound email (marks as read), PATCH to toggle is_read."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request, pk):
        try:
            email = InboundEmail.objects.select_related("client").get(id=pk, tenant=request.tenant)
        except InboundEmail.DoesNotExist:
            return Response({"detail": "Nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        if not email.is_read:
            email.is_read = True
            email.save(update_fields=["is_read", "updated_at"])
        return Response(InboundEmailSerializer(email).data)

    def patch(self, request, pk):
        try:
            email = InboundEmail.objects.get(id=pk, tenant=request.tenant)
        except InboundEmail.DoesNotExist:
            return Response({"detail": "Nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        if "is_read" in request.data:
            email.is_read = bool(request.data["is_read"])
            email.save(update_fields=["is_read", "updated_at"])
        return Response(InboundEmailSerializer(email).data)


# ------------------------------------------------------------------
# WhatsApp Messages (authenticated inbox)
# ------------------------------------------------------------------


class WhatsAppMessageListView(ListAPIView):
    """Authenticated list of WhatsApp messages for the current tenant."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]
    serializer_class = WhatsAppMessageSerializer

    def get_queryset(self):
        qs = WhatsAppMessage.objects.filter(tenant=self.request.tenant).select_related("client")
        direction = self.request.query_params.get("direction")
        if direction in ("inbound", "outbound"):
            qs = qs.filter(direction=direction)
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        is_read = self.request.query_params.get("is_read")
        if is_read == "true":
            qs = qs.filter(is_read=True)
        elif is_read == "false":
            qs = qs.filter(is_read=False)
        return qs


class WhatsAppMessageDetailView(APIView):
    """GET single WhatsApp message (marks as read), PATCH to toggle is_read."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request, pk):
        try:
            msg = WhatsAppMessage.objects.select_related("client").get(id=pk, tenant=request.tenant)
        except WhatsAppMessage.DoesNotExist:
            return Response({"detail": "Nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        if not msg.is_read:
            msg.is_read = True
            msg.save(update_fields=["is_read", "updated_at"])
        return Response(WhatsAppMessageSerializer(msg).data)

    def patch(self, request, pk):
        try:
            msg = WhatsAppMessage.objects.get(id=pk, tenant=request.tenant)
        except WhatsAppMessage.DoesNotExist:
            return Response({"detail": "Nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        if "is_read" in request.data:
            msg.is_read = bool(request.data["is_read"])
            msg.save(update_fields=["is_read", "updated_at"])
        return Response(WhatsAppMessageSerializer(msg).data)
