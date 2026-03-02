import pytest
from apps.tenants.models import Tenant


@pytest.mark.django_db
class TestTenantModel:
    def test_create_tenant(self):
        tenant = Tenant.objects.create(name="Test Agency", slug="test-agency")
        assert tenant.name == "Test Agency"
        assert tenant.slug == "test-agency"
        assert tenant.is_active is True
        assert tenant.settings == {}
        assert tenant.id is not None

    def test_str(self):
        tenant = Tenant(name="My Org")
        assert str(tenant) == "My Org"
