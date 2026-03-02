from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import HasActiveSubscription, IsTenantAdmin, IsTenantMember, IsTenantOwner

from .models import Membership
from .serializers import (
    ChangeMemberRoleSerializer,
    InviteMemberSerializer,
    MembershipSerializer,
    UserDetailSerializer,
)
from .services import UserService


@method_decorator(ensure_csrf_cookie, name="get")
class MeView(APIView):
    """Current user details + memberships."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)


class UserTenantsView(APIView):
    """List tenants the current user belongs to (for tenant switcher)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        memberships = request.user.memberships.filter(is_active=True).select_related("tenant")
        data = [
            {
                "id": str(m.tenant.id),
                "name": m.tenant.name,
                "slug": m.tenant.slug,
                "role": m.role,
            }
            for m in memberships
        ]
        return Response(data)


class MemberListView(APIView):
    """List members of the current tenant."""
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, HasActiveSubscription]

    def get(self, request):
        members = Membership.objects.filter(
            tenant=request.tenant, is_active=True
        ).select_related("user")
        serializer = MembershipSerializer(members, many=True)
        return Response(serializer.data)


class InviteMemberView(APIView):
    """Invite a new member to the tenant."""
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def post(self, request):
        serializer = InviteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = UserService.invite_member(
            tenant=request.tenant,
            email=serializer.validated_data["email"],
            role=serializer.validated_data["role"],
            invited_by=request.user,
        )

        if membership is None:
            return Response(
                {"detail": "User is already a member of this organization."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )


class MemberDetailView(APIView):
    """Update or remove a member."""
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin, HasActiveSubscription]

    def patch(self, request, pk):
        """Change member role (owner only)."""
        try:
            membership = Membership.objects.get(pk=pk, tenant=request.tenant)
        except Membership.DoesNotExist:
            return Response({"detail": "Member not found."}, status=status.HTTP_404_NOT_FOUND)

        # Only owners can change roles
        if not request.user.is_staff:
            is_owner = request.user.memberships.filter(
                tenant=request.tenant, role="owner", is_active=True
            ).exists()
            if not is_owner:
                return Response(
                    {"detail": "Only owners can change roles."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = ChangeMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = UserService.change_role(
            membership=membership,
            new_role=serializer.validated_data["role"],
            changed_by=request.user,
        )
        return Response(MembershipSerializer(membership).data)

    def delete(self, request, pk):
        """Remove a member."""
        try:
            membership = Membership.objects.get(pk=pk, tenant=request.tenant)
        except Membership.DoesNotExist:
            return Response({"detail": "Member not found."}, status=status.HTTP_404_NOT_FOUND)

        # Can't remove yourself
        if membership.user == request.user:
            return Response(
                {"detail": "You cannot remove yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        UserService.remove_member(membership=membership, removed_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
