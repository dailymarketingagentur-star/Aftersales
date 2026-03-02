import pytest
from apps.users.models import Membership, User


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert str(user) == "test@example.com"

    def test_email_is_username(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        assert user.USERNAME_FIELD == "email"


@pytest.mark.django_db
class TestMembershipModel:
    def test_create_membership(self, user_factory, tenant_factory):
        user = user_factory()
        tenant = tenant_factory()
        membership = Membership.objects.create(user=user, tenant=tenant, role="admin")
        assert membership.role == "admin"
        assert membership.is_active is True
        assert str(membership) == f"{user.email} - {tenant.name} (admin)"
