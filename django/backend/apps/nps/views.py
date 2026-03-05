from django.utils.text import slugify
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import Client
from apps.common.permissions import HasActiveSubscription, IsTenantAdmin, IsTenantMember
from apps.nps.models import NPSCampaign, NPSResponse, NPSSurvey, TestimonialRequest
from apps.nps.serializers import (
    NPSCampaignCreateSerializer,
    NPSCampaignSerializer,
    NPSDashboardSerializer,
    NPSResponseSerializer,
    NPSSurveySerializer,
    NPSTrendPointSerializer,
    PreviewNPSSurveySerializer,
    PublicSurveySerializer,
    SendSurveySerializer,
    SubmitResponseSerializer,
    TestimonialCreateSerializer,
    TestimonialRequestSerializer,
)
from apps.nps.services import NPSService


# ---------------------------------------------------------------------------
# Public endpoints (no JWT, no X-Tenant-ID)
# ---------------------------------------------------------------------------
class PublicSurveyView(APIView):
    """GET /api/v1/nps/public/<token>/ — Survey metadata for the public page."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, token):
        try:
            survey = NPSSurvey.objects.select_related("client", "tenant").get(token=token)
        except NPSSurvey.DoesNotExist:
            return Response({"detail": "Umfrage nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "tenant_name": survey.tenant.name,
            "client_first_name": survey.client.contact_first_name or survey.client.name.split()[0] if survey.client.name else "",
            "is_expired": survey.is_expired,
            "is_responded": survey.status == NPSSurvey.Status.RESPONDED,
        }
        serializer = PublicSurveySerializer(data)
        return Response(serializer.data)


class PublicSurveyRespondView(APIView):
    """POST /api/v1/nps/public/<token>/respond/ — Submit NPS score + comment."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, token):
        try:
            survey = NPSSurvey.objects.select_related("client", "tenant", "task").get(token=token)
        except NPSSurvey.DoesNotExist:
            return Response({"detail": "Umfrage nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SubmitResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip_address = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        user_agent = request.META.get("HTTP_USER_AGENT", "")

        try:
            response = NPSService.submit_response(
                survey=survey,
                score=serializer.validated_data["score"],
                comment=serializer.validated_data.get("comment", ""),
                ip_address=ip_address or None,
                user_agent=user_agent,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Trigger async follow-up processing
        from apps.nps.tasks import process_nps_followup

        process_nps_followup.delay(str(response.id))

        return Response({
            "detail": "Vielen Dank fuer Ihr Feedback!",
            "score": response.score,
            "segment": response.segment,
        }, status=status.HTTP_201_CREATED)


class PublicSurveyCommentView(APIView):
    """PATCH /api/v1/nps/public/<token>/comment/ — Add comment to an already submitted response."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def patch(self, request, token):
        try:
            survey = NPSSurvey.objects.get(token=token, status=NPSSurvey.Status.RESPONDED)
        except NPSSurvey.DoesNotExist:
            return Response({"detail": "Umfrage nicht gefunden oder noch nicht beantwortet."}, status=status.HTTP_404_NOT_FOUND)

        comment = request.data.get("comment", "").strip()
        if not comment:
            return Response({"detail": "Kommentar darf nicht leer sein."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            nps_response = NPSResponse.objects.get(survey=survey)
        except NPSResponse.DoesNotExist:
            return Response({"detail": "Antwort nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        nps_response.comment = comment
        nps_response.save(update_fields=["comment"])

        return Response({"detail": "Kundenstimme gespeichert. Vielen Dank!"})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class NPSDashboardView(APIView):
    """GET /api/v1/nps/dashboard/ — NPS score + segment distribution."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request):
        nps_data = NPSService.calculate_nps(request.tenant)
        sent = NPSService.surveys_sent_count(request.tenant)
        responded = NPSService.surveys_responded_count(request.tenant)
        response_rate = round(responded / sent * 100, 1) if sent > 0 else 0

        data = {
            **nps_data,
            "surveys_sent": sent,
            "surveys_responded": responded,
            "response_rate": response_rate,
        }
        serializer = NPSDashboardSerializer(data)
        return Response(serializer.data)


class NPSTrendView(APIView):
    """GET /api/v1/nps/dashboard/trend/ — Monthly NPS trend."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request):
        months = int(request.query_params.get("months", 12))
        trend = NPSService.nps_over_time(request.tenant, months=months)
        serializer = NPSTrendPointSerializer(trend, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Campaigns CRUD
# ---------------------------------------------------------------------------
class NPSCampaignListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def get(self, request):
        campaigns = NPSCampaign.objects.filter(tenant=request.tenant).order_by("-created_at")
        serializer = NPSCampaignSerializer(campaigns, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = NPSCampaignCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Resolve email_template FK
        email_template = None
        template_id = data.pop("email_template", None)
        if template_id:
            from apps.emails.models import EmailTemplate

            try:
                email_template = EmailTemplate.objects.get(id=template_id)
            except EmailTemplate.DoesNotExist:
                return Response({"detail": "E-Mail-Vorlage nicht gefunden."}, status=status.HTTP_400_BAD_REQUEST)

        slug = slugify(data["name"])
        # Collision check
        counter = 1
        original_slug = slug
        while NPSCampaign.objects.filter(tenant=request.tenant, slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

        campaign = NPSCampaign.objects.create(
            tenant=request.tenant,
            slug=slug,
            email_template=email_template,
            **data,
        )
        return Response(NPSCampaignSerializer(campaign).data, status=status.HTTP_201_CREATED)


class NPSCampaignDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def get(self, request, pk):
        try:
            campaign = NPSCampaign.objects.get(tenant=request.tenant, pk=pk)
        except NPSCampaign.DoesNotExist:
            return Response({"detail": "Kampagne nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        return Response(NPSCampaignSerializer(campaign).data)

    def patch(self, request, pk):
        try:
            campaign = NPSCampaign.objects.get(tenant=request.tenant, pk=pk)
        except NPSCampaign.DoesNotExist:
            return Response({"detail": "Kampagne nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        for field in ["name", "trigger_type", "day_offset", "repeat_interval_days", "is_active"]:
            if field in request.data:
                setattr(campaign, field, request.data[field])

        if "email_template" in request.data:
            template_id = request.data["email_template"]
            if template_id:
                from apps.emails.models import EmailTemplate

                try:
                    campaign.email_template = EmailTemplate.objects.get(id=template_id)
                except EmailTemplate.DoesNotExist:
                    return Response({"detail": "E-Mail-Vorlage nicht gefunden."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                campaign.email_template = None

        campaign.save()
        return Response(NPSCampaignSerializer(campaign).data)

    def delete(self, request, pk):
        try:
            campaign = NPSCampaign.objects.get(tenant=request.tenant, pk=pk)
        except NPSCampaign.DoesNotExist:
            return Response({"detail": "Kampagne nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        campaign.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Surveys
# ---------------------------------------------------------------------------
class NPSSurveyListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request):
        qs = NPSSurvey.objects.filter(tenant=request.tenant).select_related("client")

        # Filters
        client_slug = request.query_params.get("client")
        if client_slug:
            qs = qs.filter(client__slug=client_slug)

        survey_status = request.query_params.get("status")
        if survey_status:
            qs = qs.filter(status=survey_status)

        qs = qs.order_by("-created_at")[:100]
        serializer = NPSSurveySerializer(qs, many=True)
        return Response(serializer.data)


class SendSurveyView(APIView):
    """POST /api/v1/nps/surveys/send/ — Manually send a survey to a client."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def post(self, request):
        serializer = SendSurveySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_id = serializer.validated_data["client_id"]
        try:
            client = Client.objects.get(tenant=request.tenant, id=client_id)
        except Client.DoesNotExist:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        recipient_email = serializer.validated_data.get("recipient_email")
        actual_email = recipient_email or client.contact_email

        if not actual_email:
            return Response({"detail": "Mandant hat keine E-Mail-Adresse hinterlegt."}, status=status.HTTP_400_BAD_REQUEST)

        campaign = None
        campaign_id = serializer.validated_data.get("campaign_id")
        if campaign_id:
            try:
                campaign = NPSCampaign.objects.get(tenant=request.tenant, id=campaign_id)
            except NPSCampaign.DoesNotExist:
                return Response({"detail": "Kampagne nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        try:
            survey = NPSService.send_survey(
                tenant=request.tenant, client=client, campaign=campaign, recipient_email=recipient_email,
            )
        except Exception as e:
            return Response({"detail": f"Umfrage konnte nicht gesendet werden: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Activity log
        from apps.tasks.models import ClientActivity

        ClientActivity.objects.create(
            tenant=request.tenant,
            client=client,
            activity_type=ClientActivity.ActivityType.NPS_SENT,
            content=f"NPS-Umfrage gesendet an {actual_email}.",
            author=request.user,
        )

        return Response(NPSSurveySerializer(survey).data, status=status.HTTP_201_CREATED)


class PreviewSurveyView(APIView):
    """POST /api/v1/nps/surveys/preview/ — Render NPS email preview without sending."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def post(self, request):
        serializer = PreviewNPSSurveySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_id = serializer.validated_data["client_id"]
        try:
            client = Client.objects.get(tenant=request.tenant, id=client_id)
        except Client.DoesNotExist:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        preview = NPSService.preview_survey(tenant=request.tenant, client=client)
        return Response(preview)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------
class NPSResponseListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request):
        qs = NPSResponse.objects.filter(tenant=request.tenant).select_related("client")

        segment = request.query_params.get("segment")
        if segment:
            qs = qs.filter(segment=segment)

        client_slug = request.query_params.get("client")
        if client_slug:
            qs = qs.filter(client__slug=client_slug)

        qs = qs.order_by("-responded_at")[:100]
        serializer = NPSResponseSerializer(qs, many=True)
        return Response(serializer.data)


class NPSResponseDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request, pk):
        try:
            response = NPSResponse.objects.select_related("client").get(tenant=request.tenant, pk=pk)
        except NPSResponse.DoesNotExist:
            return Response({"detail": "Antwort nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        return Response(NPSResponseSerializer(response).data)


# ---------------------------------------------------------------------------
# Testimonials
# ---------------------------------------------------------------------------
class TestimonialListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request):
        qs = TestimonialRequest.objects.filter(tenant=request.tenant).select_related("client").order_by("-created_at")

        testimonial_status = request.query_params.get("status")
        if testimonial_status:
            qs = qs.filter(status=testimonial_status)

        qs = qs[:100]
        serializer = TestimonialRequestSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TestimonialCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_id = serializer.validated_data["client_id"]
        try:
            client = Client.objects.get(tenant=request.tenant, id=client_id)
        except Client.DoesNotExist:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        nps_response = None
        nps_response_id = serializer.validated_data.get("nps_response_id")
        if nps_response_id:
            try:
                nps_response = NPSResponse.objects.get(tenant=request.tenant, id=nps_response_id)
            except NPSResponse.DoesNotExist:
                pass

        testimonial = TestimonialRequest.objects.create(
            tenant=request.tenant,
            client=client,
            nps_response=nps_response,
            request_type=serializer.validated_data.get("request_type", "written"),
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(TestimonialRequestSerializer(testimonial).data, status=status.HTTP_201_CREATED)


class TestimonialDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def patch(self, request, pk):
        try:
            testimonial = TestimonialRequest.objects.get(tenant=request.tenant, pk=pk)
        except TestimonialRequest.DoesNotExist:
            return Response({"detail": "Testimonial nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        for field in ["status", "content", "platform_url", "notes", "request_type"]:
            if field in request.data:
                setattr(testimonial, field, request.data[field])

        if request.data.get("status") == "received" and not testimonial.received_at:
            from django.utils import timezone

            testimonial.received_at = timezone.now()

        testimonial.save()
        return Response(TestimonialRequestSerializer(testimonial).data)


# ---------------------------------------------------------------------------
# Per-Client NPS history
# ---------------------------------------------------------------------------
class ClientNPSView(APIView):
    """GET /api/v1/nps/clients/<slug>/ — NPS history for a specific client."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request, slug):
        try:
            client = Client.objects.get(tenant=request.tenant, slug=slug)
        except Client.DoesNotExist:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        responses = NPSResponse.objects.filter(
            tenant=request.tenant,
            client=client,
        ).order_by("-responded_at")

        surveys = NPSSurvey.objects.filter(
            tenant=request.tenant,
            client=client,
        ).order_by("-created_at")[:10]

        testimonials = TestimonialRequest.objects.filter(
            tenant=request.tenant,
            client=client,
        ).order_by("-created_at")

        return Response({
            "responses": NPSResponseSerializer(responses, many=True).data,
            "surveys": NPSSurveySerializer(surveys, many=True).data,
            "testimonials": TestimonialRequestSerializer(testimonials, many=True).data,
        })
