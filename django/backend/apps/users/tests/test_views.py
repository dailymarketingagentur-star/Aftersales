import pytest
from rest_framework import status

from apps.emails.models import EmailTemplate
from apps.users.models import Membership


@pytest.fixture
def invite_template(db):
    """System team-invite template required by UserService.invite_member."""
    return EmailTemplate.objects.create(
        tenant=None,
        slug="team-invite",
        name="Team-Einladung",
        subject="Einladung zu {{TENANT_NAME}}",
        body_html="<p>{{INVITED_BY}} laedt Sie zu {{TENANT_NAME}} ein.</p>",
        variables=["INVITED_BY", "TENANT_NAME", "INVITE_URL"],
    )


@pytest.mark.django_db
class TestMeView:
    def test_get_me(self, authenticated_client, user):
        response = authenticated_client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_get_me_unauthenticated(self, api_client):
        response = api_client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserTenantsView:
    def test_list_tenants(self, authenticated_client, user, tenant_factory):
        t1 = tenant_factory(name="Agency A")
        t2 = tenant_factory(name="Agency B")
        Membership.objects.create(user=user, tenant=t1, role="owner")
        Membership.objects.create(user=user, tenant=t2, role="member")

        response = authenticated_client.get("/api/v1/auth/tenants/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


@pytest.mark.django_db
class TestMemberListView:
    def test_list_members(self, authenticated_client, user, tenant_factory, user_factory):
        tenant = tenant_factory()
        Membership.objects.create(user=user, tenant=tenant, role="owner")
        other_user = user_factory()
        Membership.objects.create(user=other_user, tenant=tenant, role="member")

        response = authenticated_client.get(
            "/api/v1/members/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


@pytest.mark.django_db
class TestInviteMemberView:
    def test_invite_member(self, authenticated_client, user, tenant_factory, invite_template):
        from unittest.mock import patch

        tenant = tenant_factory()
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-invite"
            response = authenticated_client.post(
                "/api/v1/members/invite/",
                {"email": "newuser@example.com", "role": "member"},
                format="json",
                HTTP_X_TENANT_ID=str(tenant.id),
            )
        assert response.status_code == status.HTTP_201_CREATED

    def test_invite_member_as_member_fails(self, authenticated_client, user, tenant_factory):
        tenant = tenant_factory()
        Membership.objects.create(user=user, tenant=tenant, role="member")

        response = authenticated_client.post(
            "/api/v1/members/invite/",
            {"email": "fail@example.com", "role": "member"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTenantIsolation:
    """Verify members of one tenant cannot access another tenant's data."""

    def test_cannot_access_other_tenant(self, authenticated_client, user, tenant_factory):
        my_tenant = tenant_factory(name="My Agency")
        other_tenant = tenant_factory(name="Other Agency")
        Membership.objects.create(user=user, tenant=my_tenant, role="member")

        response = authenticated_client.get(
            "/api/v1/members/",
            HTTP_X_TENANT_ID=str(other_tenant.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
