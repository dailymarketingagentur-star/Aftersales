"""Global pytest fixtures for the Aftersales SaaS backend."""

import pytest
from apps.billing.models import TenantSubscription
from apps.tenants.models import Tenant
from apps.users.models import User


@pytest.fixture
def user_factory(db):
    """Factory to create test users."""

    def create_user(
        email=None,
        password="testpass123",
        first_name="Test",
        last_name="User",
        **kwargs,
    ):
        if email is None:
            email = f"user-{User.objects.count() + 1}@example.com"
        return User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **kwargs,
        )

    return create_user


@pytest.fixture
def tenant_factory(db):
    """Factory to create test tenants with an active subscription."""

    def create_tenant(name=None, slug=None, subscription_status="active", **kwargs):
        count = Tenant.objects.count() + 1
        if name is None:
            name = f"Test Tenant {count}"
        if slug is None:
            slug = f"test-tenant-{count}"
        tenant = Tenant.objects.create(name=name, slug=slug, **kwargs)
        TenantSubscription.objects.create(
            tenant=tenant,
            status=subscription_status,
            plan_name="Test Plan",
        )
        return tenant

    return create_tenant


@pytest.fixture
def user(user_factory):
    """Single test user."""
    return user_factory()


@pytest.fixture
def tenant(tenant_factory):
    """Single test tenant."""
    return tenant_factory()


@pytest.fixture
def api_client():
    """DRF API client."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """API client authenticated as test user."""
    api_client.force_authenticate(user=user)
    return api_client
