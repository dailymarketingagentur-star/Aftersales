import pytest
from rest_framework import status

from apps.audit.services import AuditService
from apps.users.models import Membership


@pytest.mark.django_db
class TestAuditEventListView:
    def test_list_audit_events(self, authenticated_client, user, tenant_factory):
        tenant = tenant_factory()
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        AuditService.log(
            tenant=tenant,
            user=user,
            action="test.action",
            entity_type="test",
            entity_id="123",
        )

        response = authenticated_client.get(
            "/api/v1/audit/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["action"] == "test.action"

    def test_audit_isolation(self, authenticated_client, user, tenant_factory, user_factory):
        """Audit events from one tenant must not leak to another."""
        tenant_a = tenant_factory(name="Agency A")
        tenant_b = tenant_factory(name="Agency B")
        Membership.objects.create(user=user, tenant=tenant_a, role="admin")

        other_user = user_factory()
        AuditService.log(
            tenant=tenant_b,
            user=other_user,
            action="secret.action",
            entity_type="secret",
        )

        response = authenticated_client.get(
            "/api/v1/audit/",
            HTTP_X_TENANT_ID=str(tenant_a.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_member_cannot_access_audit(self, authenticated_client, user, tenant_factory):
        """Only admins+ can access audit logs."""
        tenant = tenant_factory()
        Membership.objects.create(user=user, tenant=tenant, role="member")

        response = authenticated_client.get(
            "/api/v1/audit/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
