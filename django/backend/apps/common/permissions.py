from rest_framework.permissions import BasePermission

from apps.common.exceptions import SubscriptionRequired


class HasActiveSubscription(BasePermission):
    """
    Returns 402 if the tenant has no active subscription.
    Staff/superusers bypass this check.
    Runs AFTER DRF authentication so request.user is available.
    """

    def has_permission(self, request, view):
        # No tenant set — let other permissions handle it
        if not hasattr(request, "tenant") or request.tenant is None:
            return True

        # Staff bypass
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return True

        try:
            if request.tenant.subscription.is_active:
                return True
        except Exception:
            pass

        raise SubscriptionRequired()


class IsTenantMember(BasePermission):
    """Allows access to members of the current tenant."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        if not hasattr(request, "tenant") or request.tenant is None:
            return False
        return request.user.memberships.filter(
            tenant=request.tenant, is_active=True
        ).exists()


class IsTenantAdmin(BasePermission):
    """Allows access to admins and owners of the current tenant."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        if not hasattr(request, "tenant") or request.tenant is None:
            return False
        return request.user.memberships.filter(
            tenant=request.tenant,
            is_active=True,
            role__in=["owner", "admin"],
        ).exists()


class IsTenantOwner(BasePermission):
    """Allows access only to owners of the current tenant."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        if not hasattr(request, "tenant") or request.tenant is None:
            return False
        return request.user.memberships.filter(
            tenant=request.tenant,
            is_active=True,
            role="owner",
        ).exists()
