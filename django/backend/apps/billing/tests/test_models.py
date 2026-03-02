import pytest


@pytest.mark.django_db
class TestTenantSubscription:
    def test_is_active_when_active(self, tenant_factory):
        tenant = tenant_factory(subscription_status="active")
        assert tenant.subscription.is_active is True

    def test_is_active_when_trialing(self, tenant_factory):
        tenant = tenant_factory(subscription_status="trialing")
        assert tenant.subscription.is_active is True

    def test_not_active_when_canceled(self, tenant_factory):
        tenant = tenant_factory(subscription_status="canceled")
        assert tenant.subscription.is_active is False

    def test_not_active_when_none(self, tenant_factory):
        tenant = tenant_factory(subscription_status="none")
        assert tenant.subscription.is_active is False
