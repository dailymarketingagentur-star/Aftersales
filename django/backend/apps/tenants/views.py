from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Tenant
from .serializers import TenantCreateSerializer, TenantSerializer, TenantUpdateSerializer
from .services import TenantService


class TenantListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Create a new tenant. The requesting user becomes the owner."""
        serializer = TenantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant = TenantService.create_tenant(
            name=serializer.validated_data["name"],
            owner_user=request.user,
        )
        return Response(TenantSerializer(tenant).data, status=status.HTTP_201_CREATED)


class TenantDetailView(APIView):
    """
    Tenant detail view. Membership is checked inline because
    /api/v1/tenants/ is in TenantMiddleware EXEMPT_PATHS (needed for
    POST create), so request.tenant is not set for this path.
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_tenant_or_404(self, pk):
        try:
            return Tenant.objects.get(pk=pk, is_active=True)
        except Tenant.DoesNotExist:
            return None

    def _check_membership(self, user, tenant, require_admin=False):
        """Check membership inline. Staff bypasses."""
        if user.is_staff:
            return True
        qs = user.memberships.filter(tenant=tenant, is_active=True)
        if require_admin:
            qs = qs.filter(role__in=["owner", "admin"])
        return qs.exists()

    def get(self, request, pk):
        """Retrieve tenant details (member+)."""
        tenant = self._get_tenant_or_404(pk)
        if tenant is None:
            return Response({"detail": "Tenant not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._check_membership(request.user, tenant):
            return Response({"detail": "You are not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)
        return Response(TenantSerializer(tenant).data)

    def patch(self, request, pk):
        """Update tenant (admin+ only)."""
        tenant = self._get_tenant_or_404(pk)
        if tenant is None:
            return Response({"detail": "Tenant not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._check_membership(request.user, tenant, require_admin=True):
            return Response({"detail": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        serializer = TenantUpdateSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        tenant = TenantService.update_tenant(tenant, serializer.validated_data, request.user)
        return Response(TenantSerializer(tenant).data)
