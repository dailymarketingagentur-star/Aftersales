"""Tests for email provider API endpoints."""

from unittest.mock import patch

import pytest
from rest_framework import status

from apps.emails.models import EmailProviderConnection, EmailProviderType
from apps.users.models import Membership


@pytest.fixture
def owner_setup(user, tenant_factory):
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="owner")
    return tenant


@pytest.fixture
def admin_setup(user, tenant_factory):
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="admin")
    return tenant


@pytest.fixture
def member_setup(user, tenant_factory):
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="member")
    return tenant


@pytest.fixture
def smtp_data():
    return {
        "label": "Mein SMTP",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "user@example.com",
        "smtp_password": "geheim123",
        "smtp_use_tls": True,
        "from_email": "noreply@example.com",
        "from_name": "Beispiel GmbH",
    }


@pytest.fixture
def sendgrid_data():
    return {
        "label": "Mein SendGrid",
        "sendgrid_api_key": "SG.testkey123",
        "from_email": "noreply@example.com",
        "from_name": "Beispiel GmbH",
    }


@pytest.mark.django_db
class TestSmtpProviderCRUD:
    def test_get_not_configured(self, authenticated_client, owner_setup):
        resp = authenticated_client.get(
            "/api/v1/emails/providers/smtp/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_create_smtp(self, authenticated_client, owner_setup, smtp_data):
        resp = authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["smtp_host"] == "smtp.example.com"
        assert resp.data["is_active"] is False
        # Password must never be in response
        assert "smtp_password" not in resp.data
        assert "smtp_password_encrypted" not in resp.data

    def test_update_smtp(self, authenticated_client, owner_setup, smtp_data):
        # Create first
        authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        # Update
        smtp_data["smtp_host"] = "mail.updated.com"
        smtp_data["smtp_password"] = ""  # Don't change password
        resp = authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["smtp_host"] == "mail.updated.com"

    def test_get_smtp(self, authenticated_client, owner_setup, smtp_data):
        authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        resp = authenticated_client.get(
            "/api/v1/emails/providers/smtp/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["provider_type"] == "smtp"

    def test_delete_smtp(self, authenticated_client, owner_setup, smtp_data):
        authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        resp = authenticated_client.delete(
            "/api/v1/emails/providers/smtp/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not EmailProviderConnection.objects.filter(tenant=owner_setup).exists()


@pytest.mark.django_db
class TestSendGridProviderCRUD:
    def test_create_sendgrid(self, authenticated_client, owner_setup, sendgrid_data):
        resp = authenticated_client.put(
            "/api/v1/emails/providers/sendgrid/",
            sendgrid_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert "sendgrid_api_key" not in resp.data

    def test_delete_sendgrid(self, authenticated_client, owner_setup, sendgrid_data):
        authenticated_client.put(
            "/api/v1/emails/providers/sendgrid/",
            sendgrid_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        resp = authenticated_client.delete(
            "/api/v1/emails/providers/sendgrid/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestProviderActivation:
    def test_activate_smtp(self, authenticated_client, owner_setup, smtp_data):
        authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        resp = authenticated_client.post(
            "/api/v1/emails/providers/smtp/activate/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["is_active"] is True

    def test_activate_deactivates_other(self, authenticated_client, owner_setup, smtp_data, sendgrid_data):
        # Create and activate SMTP
        authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        authenticated_client.post(
            "/api/v1/emails/providers/smtp/activate/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        # Create and activate SendGrid
        authenticated_client.put(
            "/api/v1/emails/providers/sendgrid/",
            sendgrid_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        resp = authenticated_client.post(
            "/api/v1/emails/providers/sendgrid/activate/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["is_active"] is True
        # SMTP should now be inactive
        smtp = EmailProviderConnection.objects.get(tenant=owner_setup, provider_type=EmailProviderType.SMTP)
        assert smtp.is_active is False


@pytest.mark.django_db
class TestProviderTest:
    @patch("apps.emails.provider_service.smtplib.SMTP")
    def test_smtp_test(self, mock_smtp, authenticated_client, owner_setup, smtp_data):
        authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        resp = authenticated_client.post(
            "/api/v1/emails/providers/smtp/test/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["success"] is True

    def test_test_not_configured(self, authenticated_client, owner_setup):
        resp = authenticated_client.post(
            "/api/v1/emails/providers/smtp/test/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProviderPermissions:
    def test_admin_cannot_manage_providers(self, authenticated_client, admin_setup, smtp_data):
        """Only owners can manage email providers."""
        resp = authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(admin_setup.id),
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_provider_list(self, authenticated_client, owner_setup, smtp_data, sendgrid_data):
        authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        authenticated_client.put(
            "/api/v1/emails/providers/sendgrid/",
            sendgrid_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        resp = authenticated_client.get(
            "/api/v1/emails/providers/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 2


@pytest.mark.django_db
class TestProviderStatus:
    """Tests for GET /api/v1/emails/providers/status/ — available to all members."""

    def test_no_provider_returns_false(self, authenticated_client, member_setup):
        resp = authenticated_client.get(
            "/api/v1/emails/providers/status/",
            HTTP_X_TENANT_ID=str(member_setup.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["has_active_provider"] is False
        assert resp.data["provider_type"] is None
        assert resp.data["from_email"] is None

    def test_active_provider_returns_true(self, authenticated_client, owner_setup, smtp_data):
        # Create and activate SMTP
        authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        authenticated_client.post(
            "/api/v1/emails/providers/smtp/activate/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )

        resp = authenticated_client.get(
            "/api/v1/emails/providers/status/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["has_active_provider"] is True
        assert resp.data["provider_type"] == "smtp"
        assert "noreply@example.com" in resp.data["from_email"]

    def test_inactive_provider_returns_false(self, authenticated_client, owner_setup, smtp_data):
        # Create but don't activate
        authenticated_client.put(
            "/api/v1/emails/providers/smtp/",
            smtp_data,
            format="json",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )

        resp = authenticated_client.get(
            "/api/v1/emails/providers/status/",
            HTTP_X_TENANT_ID=str(owner_setup.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["has_active_provider"] is False
