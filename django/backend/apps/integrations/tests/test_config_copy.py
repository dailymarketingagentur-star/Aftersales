"""Tests for the integration config copy feature."""

import pytest
from django.test import override_settings

from apps.audit.models import AuditEvent
from apps.emails.models import EmailProviderConnection
from apps.integrations.config_copy_service import ConfigCopyService
from apps.integrations.models import ActionTemplate, JiraConnection
from apps.users.models import Membership


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestGetCopyableSources:
    def test_only_owned_tenants(self, source_target_setup, tenant_factory):
        """Admin-only tenants should not be returned."""
        user = source_target_setup["user"]
        target = source_target_setup["target"]

        # Create a tenant where user is only admin
        admin_tenant = tenant_factory(name="Admin Tenant", slug="admin-tenant")
        Membership.objects.create(user=user, tenant=admin_tenant, role="admin")
        # Give it a Jira connection so it would show up if ownership wasn't checked
        conn = JiraConnection(tenant=admin_tenant, jira_url="https://x.atlassian.net", jira_email="a@b.com")
        conn.set_token("token")
        conn.save()

        sources = ConfigCopyService.get_copyable_sources(user=user, exclude_tenant=target)
        tenant_ids = [s["tenant_id"] for s in sources]
        assert str(admin_tenant.id) not in tenant_ids
        assert str(source_target_setup["source"].id) in tenant_ids

    def test_only_tenants_with_configs(self, user, tenant_factory):
        """Empty tenants (no configs) should be omitted."""
        empty = tenant_factory(name="Empty Tenant", slug="empty-tenant")
        Membership.objects.create(user=user, tenant=empty, role="owner")
        target = tenant_factory(name="Target", slug="target-x")
        Membership.objects.create(user=user, tenant=target, role="owner")

        sources = ConfigCopyService.get_copyable_sources(user=user, exclude_tenant=target)
        tenant_ids = [s["tenant_id"] for s in sources]
        assert str(empty.id) not in tenant_ids


class TestCopyEmailProvider:
    def test_copies_with_password(self, source_target_setup):
        """Copies SMTP provider with correct password, is_active=False."""
        setup = source_target_setup
        result = ConfigCopyService.copy_config(
            source_tenant=setup["source"],
            target_tenant=setup["target"],
            types=["email_provider"],
            overwrite=False,
            user=setup["user"],
        )
        assert len(result["copied"]) == 1
        assert "smtp" in result["copied"][0]

        copied = EmailProviderConnection.objects.get(tenant=setup["target"])
        assert copied.is_active is False
        assert copied.get_smtp_password() == "smtp-secret-123"
        assert copied.smtp_host == "mail.example.com"

    def test_skips_without_overwrite(self, source_target_setup):
        """If target already has a provider of same type, skip without overwrite."""
        setup = source_target_setup
        EmailProviderConnection.objects.create(
            tenant=setup["target"],
            provider_type="smtp",
            label="Existing SMTP",
            from_email="old@example.com",
        )
        result = ConfigCopyService.copy_config(
            source_tenant=setup["source"],
            target_tenant=setup["target"],
            types=["email_provider"],
            overwrite=False,
            user=setup["user"],
        )
        assert len(result["skipped"]) == 1
        assert len(result["copied"]) == 0
        # Original still exists
        assert EmailProviderConnection.objects.filter(
            tenant=setup["target"], label="Existing SMTP"
        ).exists()

    def test_overwrites(self, source_target_setup):
        """With overwrite=True, existing is deleted and replaced."""
        setup = source_target_setup
        EmailProviderConnection.objects.create(
            tenant=setup["target"],
            provider_type="smtp",
            label="Old SMTP",
            from_email="old@example.com",
        )
        result = ConfigCopyService.copy_config(
            source_tenant=setup["source"],
            target_tenant=setup["target"],
            types=["email_provider"],
            overwrite=True,
            user=setup["user"],
        )
        assert len(result["copied"]) == 1
        target_provider = EmailProviderConnection.objects.get(tenant=setup["target"])
        assert target_provider.label == "Source SMTP"
        assert target_provider.is_active is False


class TestCopyJiraConnection:
    def test_copies_with_token(self, source_target_setup):
        """Copies Jira connection with correct decrypted/re-encrypted token."""
        setup = source_target_setup
        result = ConfigCopyService.copy_config(
            source_tenant=setup["source"],
            target_tenant=setup["target"],
            types=["jira_connection"],
            overwrite=False,
            user=setup["user"],
        )
        assert "jira_connection" in result["copied"]

        copied = JiraConnection.objects.get(tenant=setup["target"], is_active=True)
        assert copied.get_token() == "jira-token-456"
        assert copied.jira_url == "https://source.atlassian.net"
        assert copied.is_active is True


class TestCopyActionTemplates:
    def test_copies_as_non_system(self, source_target_setup):
        """Copies tenant templates with is_system=False."""
        setup = source_target_setup
        result = ConfigCopyService.copy_config(
            source_tenant=setup["source"],
            target_tenant=setup["target"],
            types=["action_templates"],
            overwrite=False,
            user=setup["user"],
        )
        assert any("custom-action" in c for c in result["copied"])

        copied = ActionTemplate.objects.get(tenant=setup["target"], slug="custom-action")
        assert copied.is_system is False
        assert copied.name == "Custom Action"
        assert copied.body_json == {"fields": {"summary": "{{SUMMARY}}"}}


class TestAuditLog:
    def test_creates_audit_log(self, source_target_setup):
        """Copy operation creates an audit event."""
        setup = source_target_setup
        ConfigCopyService.copy_config(
            source_tenant=setup["source"],
            target_tenant=setup["target"],
            types=["email_provider"],
            overwrite=False,
            user=setup["user"],
        )
        event = AuditEvent.objects.filter(
            tenant=setup["target"],
            action="config_copy",
            entity_type="integration_config",
        ).first()
        assert event is not None
        assert event.before["source_tenant"] == "Source Tenant"
        assert event.after["copied"] is not None


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


class TestCopyConfigSourcesAPI:
    def test_requires_owner(self, authenticated_client, admin_setup):
        """Admin (not owner) gets 403."""
        resp = authenticated_client.get(
            "/api/v1/integrations/copy-config/sources/",
            HTTP_X_TENANT_ID=str(admin_setup.id),
        )
        assert resp.status_code == 403


class TestCopyConfigAPI:
    def test_requires_owner_on_both(self, authenticated_client, source_target_setup, tenant_factory):
        """Must be owner of both source and target tenant."""
        setup = source_target_setup
        # Create a tenant the user does NOT own
        other_tenant = tenant_factory(name="Other", slug="other-tenant")
        # user is NOT a member at all

        resp = authenticated_client.post(
            "/api/v1/integrations/copy-config/",
            data={
                "source_tenant_id": str(other_tenant.id),
                "types": ["email_provider"],
                "overwrite": False,
            },
            format="json",
            HTTP_X_TENANT_ID=str(setup["target"].id),
        )
        assert resp.status_code == 403

    def test_happy_path(self, authenticated_client, source_target_setup):
        """Full copy via API returns 200 with result."""
        setup = source_target_setup
        resp = authenticated_client.post(
            "/api/v1/integrations/copy-config/",
            data={
                "source_tenant_id": str(setup["source"].id),
                "types": ["email_provider", "jira_connection", "action_templates"],
                "overwrite": False,
            },
            format="json",
            HTTP_X_TENANT_ID=str(setup["target"].id),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["copied"]) >= 3
        assert data["errors"] == []

    def test_invalid_source(self, authenticated_client, source_target_setup):
        """Non-existent source tenant returns 404."""
        setup = source_target_setup
        resp = authenticated_client.post(
            "/api/v1/integrations/copy-config/",
            data={
                "source_tenant_id": "00000000-0000-0000-0000-000000000000",
                "types": ["email_provider"],
                "overwrite": False,
            },
            format="json",
            HTTP_X_TENANT_ID=str(setup["target"].id),
        )
        assert resp.status_code == 404

    def test_empty_types(self, authenticated_client, source_target_setup):
        """Empty types list returns 400."""
        setup = source_target_setup
        resp = authenticated_client.post(
            "/api/v1/integrations/copy-config/",
            data={
                "source_tenant_id": str(setup["source"].id),
                "types": [],
                "overwrite": False,
            },
            format="json",
            HTTP_X_TENANT_ID=str(setup["target"].id),
        )
        assert resp.status_code == 400
