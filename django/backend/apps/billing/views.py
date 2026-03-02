from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsTenantAdmin, IsTenantMember

from .serializers import CheckoutSerializer, PortalSerializer, TenantSubscriptionSerializer
from .services import BillingService


class CheckoutView(APIView):
    """Create a Stripe Checkout session."""
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin]  # No subscription check

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = BillingService.create_checkout_session(
            tenant=request.tenant,
            price_id=serializer.validated_data["price_id"],
            success_url=serializer.validated_data["success_url"],
            cancel_url=serializer.validated_data["cancel_url"],
        )
        return Response({"checkout_url": session.url}, status=status.HTTP_200_OK)


class PortalView(APIView):
    """Create a Stripe Billing Portal session."""
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin]

    def post(self, request):
        serializer = PortalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = BillingService.create_portal_session(
            tenant=request.tenant,
            return_url=serializer.validated_data["return_url"],
        )

        if session is None:
            return Response(
                {"detail": "No billing account found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"portal_url": session.url}, status=status.HTTP_200_OK)


class SubscriptionStatusView(APIView):
    """Get current subscription status."""
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get(self, request):
        subscription = BillingService.sync_subscription_status(request.tenant)
        serializer = TenantSubscriptionSerializer(subscription)
        return Response(serializer.data)
