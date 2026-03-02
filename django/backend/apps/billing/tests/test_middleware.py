import pytest
from rest_framework import status

from apps.users.models import Membership


@pytest.mark.django_db
class TestSubscriptionRequiredMiddleware:
    """Test that the HasActiveSubscription permission blocks access without active subscription."""

    def test_access_denied_without_subscription(self, authenticated_client, user, tenant_factory):
        tenant = tenant_factory(subscription_status="none")
        Membership.objects.create(user=user, tenant=tenant, role="owner")

        response = authenticated_client.get(
            "/api/v1/audit/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == 402

    def test_access_allowed_with_active_subscription(self, authenticated_client, user, tenant_factory):
        tenant = tenant_factory(subscription_status="active")
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.get(
            "/api/v1/audit/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK

    def test_access_allowed_with_trialing(self, authenticated_client, user, tenant_factory):
        tenant = tenant_factory(subscription_status="trialing")
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.get(
            "/api/v1/audit/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK

    def test_staff_bypasses_subscription(self, api_client, user_factory, tenant_factory):
        staff_user = user_factory(email="staff@example.com", is_staff=True)
        tenant = tenant_factory(subscription_status="none")
        Membership.objects.create(user=staff_user, tenant=tenant, role="admin")

        api_client.force_authenticate(user=staff_user)
        response = api_client.get(
            "/api/v1/audit/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK

    def test_billing_endpoints_exempt(self, authenticated_client, user, tenant_factory):
        """Billing endpoints should work without subscription (for initial checkout)."""
        tenant = tenant_factory(subscription_status="none")
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.get(
            "/api/v1/billing/status/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        # Should not be 402
        assert response.status_code != 402
