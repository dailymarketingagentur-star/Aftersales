import calendar
from datetime import date
from decimal import Decimal

from django.db import IntegrityError
from django.db.models import Q, Sum
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import Client, ClientKeyFact, Service, ServiceType
from apps.clients.serializers import (
    ClientCreateSerializer,
    ClientKeyFactCreateSerializer,
    ClientKeyFactSerializer,
    ClientSerializer,
    ClientUpdateSerializer,
    ServiceCreateSerializer,
    ServiceSerializer,
    ServiceTypeCreateSerializer,
    ServiceTypeSerializer,
    ServiceTypeUpdateSerializer,
    ServiceUpdateSerializer,
)
from apps.clients.services import ClientService
from apps.common.permissions import HasActiveSubscription, IsTenantAdmin, IsTenantMember, IsTenantOwner


# ---------------------------------------------------------------------------
# Client views
# ---------------------------------------------------------------------------
class ClientListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def get(self, request):
        qs = Client.objects.filter(tenant=request.tenant)

        # Filters
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        tier_filter = request.query_params.get("tier")
        if tier_filter:
            qs = qs.filter(tier=tier_filter)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        serializer = ClientSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ClientCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client = ClientService.create_client(
            tenant=request.tenant,
            data=serializer.validated_data,
            user=request.user,
        )
        return Response(ClientSerializer(client).data, status=status.HTTP_201_CREATED)


class ClientDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def _get_client(self, request, slug):
        try:
            return Client.objects.get(tenant=request.tenant, slug=slug)
        except Client.DoesNotExist:
            return None

    def get(self, request, slug):
        client = self._get_client(request, slug)
        if client is None:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ClientSerializer(client).data)

    def patch(self, request, slug):
        client = self._get_client(request, slug)
        if client is None:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ClientUpdateSerializer(client, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        client = ClientService.update_client(client, serializer.validated_data, request.user)
        return Response(ClientSerializer(client).data)

    def delete(self, request, slug):
        client = self._get_client(request, slug)
        if client is None:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        ClientService.soft_delete_client(client, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Service views (nested under client)
# ---------------------------------------------------------------------------
class ServiceListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def _get_client(self, request, slug):
        try:
            return Client.objects.get(tenant=request.tenant, slug=slug)
        except Client.DoesNotExist:
            return None

    def get(self, request, slug):
        client = self._get_client(request, slug)
        if client is None:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        services = Service.objects.filter(client=client).select_related("service_type")
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)

    def post(self, request, slug):
        client = self._get_client(request, slug)
        if client is None:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ServiceCreateSerializer(data=request.data, context={"tenant": request.tenant})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        service_type = ServiceType.objects.get(id=data.pop("service_type"), tenant=request.tenant)

        service = Service.objects.create(
            tenant=request.tenant,
            client=client,
            service_type=service_type,
            **data,
        )
        return Response(
            ServiceSerializer(service).data,
            status=status.HTTP_201_CREATED,
        )


class ServiceDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def _get_service(self, request, slug, pk):
        try:
            return Service.objects.select_related("service_type", "client").get(
                client__tenant=request.tenant, client__slug=slug, pk=pk
            )
        except Service.DoesNotExist:
            return None

    def get(self, request, slug, pk):
        service = self._get_service(request, slug, pk)
        if service is None:
            return Response({"detail": "Service nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ServiceSerializer(service).data)

    def patch(self, request, slug, pk):
        service = self._get_service(request, slug, pk)
        if service is None:
            return Response({"detail": "Service nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ServiceUpdateSerializer(service, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ServiceSerializer(service).data)

    def delete(self, request, slug, pk):
        service = self._get_service(request, slug, pk)
        if service is None:
            return Response({"detail": "Service nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        service.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# ServiceType views
# ---------------------------------------------------------------------------
class ServiceTypeListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def get(self, request):
        qs = ServiceType.objects.filter(tenant=request.tenant)
        serializer = ServiceTypeSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ServiceTypeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service_type = ServiceType(
            tenant=request.tenant,
            name=serializer.validated_data["name"],
            position=serializer.validated_data.get("position", 0),
        )
        service_type.save()
        return Response(ServiceTypeSerializer(service_type).data, status=status.HTTP_201_CREATED)


class ServiceTypeDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def _get_service_type(self, request, pk):
        try:
            return ServiceType.objects.get(pk=pk, tenant=request.tenant)
        except ServiceType.DoesNotExist:
            return None

    def patch(self, request, pk):
        service_type = self._get_service_type(request, pk)
        if service_type is None:
            return Response({"detail": "Service-Typ nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ServiceTypeUpdateSerializer(service_type, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ServiceTypeSerializer(service_type).data)

    def delete(self, request, pk):
        service_type = self._get_service_type(request, pk)
        if service_type is None:
            return Response({"detail": "Service-Typ nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        if service_type.services.exists():
            return Response(
                {"detail": "Service-Typ wird verwendet und kann nicht geloescht werden."},
                status=status.HTTP_409_CONFLICT,
            )

        service_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# ClientKeyFact views (nested under client)
# ---------------------------------------------------------------------------
class ClientKeyFactListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsTenantMember(), HasActiveSubscription()]
        return [permissions.IsAuthenticated(), IsTenantAdmin(), HasActiveSubscription()]

    def _get_client(self, request, slug):
        try:
            return Client.objects.get(tenant=request.tenant, slug=slug)
        except Client.DoesNotExist:
            return None

    def get(self, request, slug):
        client = self._get_client(request, slug)
        if client is None:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        key_facts = ClientKeyFact.objects.filter(client=client)
        serializer = ClientKeyFactSerializer(key_facts, many=True)
        return Response(serializer.data)

    def post(self, request, slug):
        client = self._get_client(request, slug)
        if client is None:
            return Response({"detail": "Mandant nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ClientKeyFactCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            key_fact = ClientKeyFact.objects.create(
                tenant=request.tenant,
                client=client,
                **serializer.validated_data,
            )
        except IntegrityError:
            return Response(
                {"detail": "Ein Key-Fact mit diesem Label existiert bereits für diesen Mandanten."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(ClientKeyFactSerializer(key_fact).data, status=status.HTTP_201_CREATED)


class ClientKeyFactDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def _get_key_fact(self, request, slug, pk):
        try:
            return ClientKeyFact.objects.get(
                client__tenant=request.tenant, client__slug=slug, pk=pk
            )
        except ClientKeyFact.DoesNotExist:
            return None

    def patch(self, request, slug, pk):
        key_fact = self._get_key_fact(request, slug, pk)
        if key_fact is None:
            return Response({"detail": "Key-Fact nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ClientKeyFactSerializer(key_fact, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ClientKeyFactSerializer(key_fact).data)

    def delete(self, request, slug, pk):
        key_fact = self._get_key_fact(request, slug, pk)
        if key_fact is None:
            return Response({"detail": "Key-Fact nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        key_fact.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Cashflow Prognose
# ---------------------------------------------------------------------------
MONTH_LABELS = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


class CashflowPrognoseView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantOwner, HasActiveSubscription]

    def get(self, request):
        months = min(int(request.query_params.get("months", 12)), 36)
        future = min(int(request.query_params.get("future", 3)), 3)
        past_months = max(months - future, 0)
        today = date.today()

        qs = Service.objects.filter(
            tenant=request.tenant,
            status=Service.Status.ACTIVE,
        )

        # Optional filters
        client_id = request.query_params.get("client")
        if client_id:
            qs = qs.filter(client__id=client_id)

        service_type_id = request.query_params.get("service_type")
        if service_type_id:
            qs = qs.filter(service_type__id=service_type_id)

        services = list(qs.values("start_date", "end_date", "monthly_budget"))

        result = []
        for i in range(-past_months, future):
            month = (today.month - 1 + i) % 12 + 1
            year = today.year + (today.month - 1 + i) // 12
            month_start = date(year, month, 1)
            month_end = date(year, month, calendar.monthrange(year, month)[1])

            total = Decimal("0.00")
            for svc in services:
                svc_start = svc["start_date"] or today
                svc_end = svc["end_date"]
                if svc_start <= month_end and (svc_end is None or svc_end >= month_start):
                    total += svc["monthly_budget"]

            result.append({
                "month": f"{year}-{month:02d}",
                "label": f"{MONTH_LABELS[month - 1]} {year}",
                "total": str(total),
            })

        return Response(result)
