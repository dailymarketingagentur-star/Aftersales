import uuid
from unittest.mock import patch
from urllib.parse import quote

import pytest
from rest_framework import status

from apps.emails.models import EmailLog, EmailStatus
from apps.emails.services import EmailService


@pytest.mark.django_db
class TestTrackOpen:
    def test_returns_pixel_and_sets_opened_at(self, api_client, tenant, system_template):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-track"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        assert log.opened_at is None

        response = api_client.get(
            f"/api/v1/emails/track/{log.tracking_id}/open/",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "image/png"

        log.refresh_from_db()
        assert log.opened_at is not None

    def test_only_records_first_open(self, api_client, tenant, system_template):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-first"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        # First open
        api_client.get(f"/api/v1/emails/track/{log.tracking_id}/open/")
        log.refresh_from_db()
        first_opened = log.opened_at

        # Second open — timestamp should not change
        api_client.get(f"/api/v1/emails/track/{log.tracking_id}/open/")
        log.refresh_from_db()
        assert log.opened_at == first_opened

    def test_handles_unknown_tracking_id(self, api_client):
        response = api_client.get(
            f"/api/v1/emails/track/{uuid.uuid4()}/open/",
        )
        # Should still return pixel (no error for unknown IDs)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "image/png"

    def test_no_auth_required(self, api_client, tenant, system_template):
        """Tracking endpoints must work without authentication."""
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-noauth"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        # No authentication, no X-Tenant-ID header
        response = api_client.get(
            f"/api/v1/emails/track/{log.tracking_id}/open/",
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTrackClick:
    def test_redirects_and_sets_clicked_at(self, api_client, tenant, system_template):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-click"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        target_url = "https://example.com/landing"
        response = api_client.get(
            f"/api/v1/emails/track/{log.tracking_id}/click/?url={quote(target_url)}",
        )
        assert response.status_code == status.HTTP_302_FOUND
        assert response["Location"] == target_url

        log.refresh_from_db()
        assert log.clicked_at is not None

    def test_only_records_first_click(self, api_client, tenant, system_template):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-first-click"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        target = "https://example.com/page"
        api_client.get(f"/api/v1/emails/track/{log.tracking_id}/click/?url={quote(target)}")
        log.refresh_from_db()
        first_click = log.clicked_at

        api_client.get(f"/api/v1/emails/track/{log.tracking_id}/click/?url={quote(target)}")
        log.refresh_from_db()
        assert log.clicked_at == first_click

    def test_rejects_javascript_url(self, api_client, tenant, system_template):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-xss"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        response = api_client.get(
            f"/api/v1/emails/track/{log.tracking_id}/click/?url=javascript:alert(1)",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_empty_url(self, api_client, tenant, system_template):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-empty"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        response = api_client.get(
            f"/api/v1/emails/track/{log.tracking_id}/click/",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_no_auth_required(self, api_client, tenant, system_template):
        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-click-noauth"
            log = EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        response = api_client.get(
            f"/api/v1/emails/track/{log.tracking_id}/click/?url={quote('https://example.com')}",
        )
        assert response.status_code == status.HTTP_302_FOUND
