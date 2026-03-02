import pytest
from apps.tenants.services import TenantService
from apps.users.models import Membership


@pytest.mark.django_db
class TestTenantService:
    def test_create_tenant(self, user_factory):
        user = user_factory()
        tenant = TenantService.create_tenant(name="New Agency", owner_user=user)

        assert tenant.name == "New Agency"
        assert tenant.slug == "new-agency"
        membership = Membership.objects.get(user=user, tenant=tenant)
        assert membership.role == "owner"

    def test_create_tenant_duplicate_slug(self, user_factory):
        user = user_factory()
        TenantService.create_tenant(name="Agency", owner_user=user)
        tenant2 = TenantService.create_tenant(name="Agency", owner_user=user)
        assert tenant2.slug == "agency-1"
