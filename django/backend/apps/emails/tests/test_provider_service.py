"""Tests for EmailProviderService."""

from unittest.mock import MagicMock, patch

import pytest

from apps.emails.models import EmailProviderConnection, EmailProviderType
from apps.emails.provider_service import EmailProviderService
from apps.users.models import Membership


@pytest.fixture
def owner_setup(user, tenant_factory):
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="owner")
    return tenant


@pytest.fixture
def smtp_connection(owner_setup):
    conn = EmailProviderConnection(
        tenant=owner_setup,
        provider_type=EmailProviderType.SMTP,
        label="Test SMTP",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_use_tls=True,
        from_email="noreply@example.com",
        from_name="Test GmbH",
        is_active=True,
    )
    conn.set_smtp_password("secret123")
    conn.save()
    return conn


@pytest.fixture
def sendgrid_connection(owner_setup):
    conn = EmailProviderConnection(
        tenant=owner_setup,
        provider_type=EmailProviderType.SENDGRID,
        label="Test SendGrid",
        from_email="noreply@example.com",
        from_name="",
        is_active=False,
    )
    conn.set_sendgrid_api_key("SG.test-key-123")
    conn.save()
    return conn


@pytest.mark.django_db
class TestGetBackendForTenant:
    def test_returns_none_when_no_provider(self, owner_setup):
        backend, from_email = EmailProviderService.get_backend_for_tenant(owner_setup)
        assert backend is None
        assert from_email is None

    def test_returns_smtp_backend(self, owner_setup, smtp_connection):
        backend, from_email = EmailProviderService.get_backend_for_tenant(owner_setup)
        assert backend is not None
        assert "Test GmbH <noreply@example.com>" == from_email
        assert backend.host == "smtp.example.com"
        assert backend.port == 587

    def test_returns_none_for_inactive_provider(self, owner_setup, sendgrid_connection):
        """Only active providers are returned."""
        backend, from_email = EmailProviderService.get_backend_for_tenant(owner_setup)
        assert backend is None
        assert from_email is None

    def test_from_email_without_name(self, owner_setup):
        conn = EmailProviderConnection(
            tenant=owner_setup,
            provider_type=EmailProviderType.SMTP,
            label="SMTP",
            smtp_host="smtp.test.com",
            smtp_port=587,
            from_email="bare@test.com",
            from_name="",
            is_active=True,
        )
        conn.set_smtp_password("pw")
        conn.save()
        _, from_email = EmailProviderService.get_backend_for_tenant(owner_setup)
        assert from_email == "bare@test.com"


@pytest.mark.django_db
class TestTestConnection:
    @patch("apps.emails.provider_service.smtplib.SMTP")
    def test_smtp_success(self, mock_smtp_class, smtp_connection):
        mock_instance = MagicMock()
        mock_smtp_class.return_value = mock_instance
        success, message = EmailProviderService.test_connection(smtp_connection)
        assert success is True
        assert "erfolgreich" in message
        smtp_connection.refresh_from_db()
        assert smtp_connection.last_test_success is True

    @patch("apps.emails.provider_service.smtplib.SMTP")
    def test_smtp_failure(self, mock_smtp_class, smtp_connection):
        mock_smtp_class.side_effect = ConnectionRefusedError("Connection refused")
        success, message = EmailProviderService.test_connection(smtp_connection)
        assert success is False
        assert "Connection refused" in message
        smtp_connection.refresh_from_db()
        assert smtp_connection.last_test_success is False

    @patch("apps.emails.provider_service.requests.get")
    def test_sendgrid_success(self, mock_get, owner_setup):
        conn = EmailProviderConnection(
            tenant=owner_setup,
            provider_type=EmailProviderType.SENDGRID,
            label="SG",
            from_email="sg@test.com",
            is_active=True,
        )
        conn.set_sendgrid_api_key("SG.key")
        conn.save()
        mock_get.return_value = MagicMock(status_code=200)
        success, message = EmailProviderService.test_connection(conn)
        assert success is True
        assert "erfolgreich" in message

    @patch("apps.emails.provider_service.requests.get")
    def test_sendgrid_failure(self, mock_get, owner_setup):
        conn = EmailProviderConnection(
            tenant=owner_setup,
            provider_type=EmailProviderType.SENDGRID,
            label="SG",
            from_email="sg@test.com",
            is_active=True,
        )
        conn.set_sendgrid_api_key("SG.bad")
        conn.save()
        mock_get.return_value = MagicMock(status_code=401)
        success, message = EmailProviderService.test_connection(conn)
        assert success is False
        assert "401" in message
