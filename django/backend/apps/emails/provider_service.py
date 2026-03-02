"""Service layer for per-tenant email provider connections.

Provides:
- get_backend_for_tenant(): returns a Django email backend + from_email for the tenant
- test_connection(): tests SMTP or SendGrid connectivity
"""

import smtplib

import requests
import structlog
from django.core.mail.backends.smtp import EmailBackend as SmtpEmailBackend
from django.utils import timezone

from apps.emails.models import EmailProviderConnection, EmailProviderType

logger = structlog.get_logger()


class EmailProviderService:
    @staticmethod
    def get_backend_for_tenant(tenant):
        """Return (backend_instance, from_email) for the tenant's active provider.

        Returns (None, None) if no provider is configured — caller should
        fall back to Django's global DEFAULT_FROM_EMAIL / default backend.
        """
        conn = EmailProviderConnection.objects.filter(
            tenant=tenant, is_active=True,
        ).first()

        if conn is None:
            return None, None

        from_email = conn.from_email
        if conn.from_name:
            from_email = f"{conn.from_name} <{conn.from_email}>"

        if conn.provider_type == EmailProviderType.SMTP:
            backend = SmtpEmailBackend(
                host=conn.smtp_host,
                port=conn.smtp_port,
                username=conn.smtp_username,
                password=conn.get_smtp_password(),
                use_tls=conn.smtp_use_tls,
                use_ssl=False,
                timeout=30,
            )
            return backend, from_email

        if conn.provider_type == EmailProviderType.SENDGRID:
            try:
                from anymail.backends.sendgrid import EmailBackend as SendGridBackend
            except ImportError:
                logger.error("anymail_not_installed", tenant_id=str(tenant.id))
                return None, None

            backend = SendGridBackend(
                api_key=conn.get_sendgrid_api_key(),
            )
            return backend, from_email

        return None, None

    @staticmethod
    def test_connection(conn: EmailProviderConnection) -> tuple[bool, str]:
        """Test the provider connection. Updates last_tested_at/success/message on the model."""
        success = False
        message = ""

        try:
            if conn.provider_type == EmailProviderType.SMTP:
                success, message = EmailProviderService._test_smtp(conn)
            elif conn.provider_type == EmailProviderType.SENDGRID:
                success, message = EmailProviderService._test_sendgrid(conn)
            else:
                message = f"Unbekannter Provider-Typ: {conn.provider_type}"
        except Exception as exc:
            message = str(exc)
            logger.error("email_provider_test_error", error=message, provider=conn.provider_type)

        conn.last_tested_at = timezone.now()
        conn.last_test_success = success
        conn.last_test_message = message
        conn.save(update_fields=["last_tested_at", "last_test_success", "last_test_message"])

        return success, message

    @staticmethod
    def _test_smtp(conn: EmailProviderConnection) -> tuple[bool, str]:
        """Test SMTP connection via connect → STARTTLS → login → quit."""
        smtp = smtplib.SMTP(conn.smtp_host, conn.smtp_port, timeout=15)
        try:
            smtp.ehlo()
            if conn.smtp_use_tls:
                smtp.starttls()
                smtp.ehlo()
            password = conn.get_smtp_password()
            if conn.smtp_username and password:
                smtp.login(conn.smtp_username, password)
            return True, "SMTP-Verbindung erfolgreich."
        finally:
            try:
                smtp.quit()
            except smtplib.SMTPException:
                pass

    @staticmethod
    def _test_sendgrid(conn: EmailProviderConnection) -> tuple[bool, str]:
        """Test SendGrid connection via GET /v3/user/profile."""
        api_key = conn.get_sendgrid_api_key()
        resp = requests.get(
            "https://api.sendgrid.com/v3/user/profile",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        if resp.status_code == 200:
            return True, "SendGrid-Verbindung erfolgreich."
        return False, f"SendGrid-Fehler: HTTP {resp.status_code}"
