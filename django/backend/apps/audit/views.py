from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework.generics import ListAPIView

from apps.common.permissions import HasActiveSubscription, IsTenantAdmin

from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventListView(ListAPIView):
    """Read-only list of audit events for the current tenant."""
    serializer_class = AuditEventSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["action", "entity_type", "entity_id"]

    def get_queryset(self):
        return AuditEvent.objects.filter(
            tenant=self.request.tenant
        ).select_related("user")
