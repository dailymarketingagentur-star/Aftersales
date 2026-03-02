from decimal import Decimal

import pytest

from apps.clients.models import Client, Service, ServiceType


@pytest.mark.django_db
class TestServiceType:
    def test_auto_slug(self, tenant_factory):
        tenant = tenant_factory()
        st = ServiceType(tenant=tenant, name="SEO Beratung", position=1)
        st.save()
        assert st.slug == "seo-beratung"

    def test_unique_slug_per_tenant(self, tenant_factory):
        tenant = tenant_factory()
        st1 = ServiceType(tenant=tenant, name="SEO", position=1)
        st1.save()
        st2 = ServiceType(tenant=tenant, name="SEO", position=2)
        st2.save()
        assert st1.slug == "seo"
        assert st2.slug == "seo-1"

    def test_same_slug_different_tenants(self, tenant_factory):
        t1 = tenant_factory()
        t2 = tenant_factory()
        st1 = ServiceType(tenant=t1, name="SEO", position=1)
        st1.save()
        st2 = ServiceType(tenant=t2, name="SEO", position=1)
        st2.save()
        assert st1.slug == st2.slug == "seo"

    def test_str(self, tenant_factory):
        tenant = tenant_factory()
        st = ServiceType(tenant=tenant, name="SEA/Google Ads")
        st.save()
        assert str(st) == "SEA/Google Ads"


@pytest.mark.django_db
class TestClient:
    def test_auto_slug(self, tenant_factory):
        tenant = tenant_factory()
        client = Client(tenant=tenant, name="Acme Corp")
        client.save()
        assert client.slug == "acme-corp"

    def test_unique_slug_per_tenant(self, tenant_factory):
        tenant = tenant_factory()
        c1 = Client(tenant=tenant, name="Acme")
        c1.save()
        c2 = Client(tenant=tenant, name="Acme")
        c2.save()
        assert c1.slug == "acme"
        assert c2.slug == "acme-1"

    def test_default_status(self, tenant_factory):
        tenant = tenant_factory()
        client = Client(tenant=tenant, name="New Client")
        client.save()
        assert client.status == Client.Status.ONBOARDING

    def test_tier_calculation(self):
        assert Client._calculate_tier(Decimal("0")) == Client.Tier.BRONZE
        assert Client._calculate_tier(Decimal("2499")) == Client.Tier.BRONZE
        assert Client._calculate_tier(Decimal("2500")) == Client.Tier.SILBER
        assert Client._calculate_tier(Decimal("4999")) == Client.Tier.SILBER
        assert Client._calculate_tier(Decimal("5000")) == Client.Tier.GOLD
        assert Client._calculate_tier(Decimal("9999")) == Client.Tier.GOLD
        assert Client._calculate_tier(Decimal("10000")) == Client.Tier.PLATIN

    def test_recalculate_volume(self, tenant_factory, service_type_factory):
        tenant = tenant_factory()
        st = service_type_factory(tenant=tenant)
        client = Client.objects.create(tenant=tenant, name="Recalc Test")

        # Create active services
        Service.objects.create(
            tenant=tenant, client=client, service_type=st,
            name="S1", monthly_budget=Decimal("3000"), status="active",
        )
        Service.objects.create(
            tenant=tenant, client=client, service_type=st,
            name="S2", monthly_budget=Decimal("2000"), status="active",
        )
        # Paused service should not count
        Service.objects.create(
            tenant=tenant, client=client, service_type=st,
            name="S3", monthly_budget=Decimal("1000"), status="paused",
        )

        client.refresh_from_db()
        assert client.monthly_volume == Decimal("5000.00")
        assert client.tier == Client.Tier.GOLD


@pytest.mark.django_db
class TestService:
    def test_str(self, tenant_factory, service_type_factory):
        tenant = tenant_factory()
        st = service_type_factory(tenant=tenant, name="Webdesign")
        client = Client.objects.create(tenant=tenant, name="My Client")
        service = Service.objects.create(
            tenant=tenant, client=client, service_type=st,
            name="Website Relaunch",
        )
        assert str(service) == "Website Relaunch (My Client)"

    def test_signal_recalculates_on_save(self, tenant_factory, service_type_factory):
        tenant = tenant_factory()
        st = service_type_factory(tenant=tenant)
        client = Client.objects.create(tenant=tenant, name="Signal Test")

        Service.objects.create(
            tenant=tenant, client=client, service_type=st,
            name="S1", monthly_budget=Decimal("5000"), status="active",
        )

        client.refresh_from_db()
        assert client.monthly_volume == Decimal("5000.00")
        assert client.tier == Client.Tier.GOLD

    def test_signal_recalculates_on_delete(self, tenant_factory, service_type_factory):
        tenant = tenant_factory()
        st = service_type_factory(tenant=tenant)
        client = Client.objects.create(tenant=tenant, name="Delete Test")

        s = Service.objects.create(
            tenant=tenant, client=client, service_type=st,
            name="S1", monthly_budget=Decimal("5000"), status="active",
        )

        client.refresh_from_db()
        assert client.monthly_volume == Decimal("5000.00")

        s.delete()
        client.refresh_from_db()
        assert client.monthly_volume == Decimal("0.00")
        assert client.tier == Client.Tier.BRONZE
