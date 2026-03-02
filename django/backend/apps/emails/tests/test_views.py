import pytest
from unittest.mock import patch

from rest_framework import status

from apps.emails.models import EmailProviderConnection, EmailProviderType, EmailTemplate
from apps.users.models import Membership


@pytest.fixture
def active_smtp_provider(tenant):
    """Create an active SMTP provider for the tenant."""
    return EmailProviderConnection.objects.create(
        tenant=tenant,
        provider_type=EmailProviderType.SMTP,
        label="Test SMTP",
        from_email="noreply@example.com",
        smtp_host="smtp.example.com",
        smtp_port=587,
        is_active=True,
    )


@pytest.mark.django_db
class TestEmailTemplateListCreate:
    def test_list_templates(self, authenticated_client, user, tenant, system_template):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.get(
            "/api/v1/emails/templates/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_tenant_template(self, authenticated_client, user, tenant):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.post(
            "/api/v1/emails/templates/",
            data={
                "slug": "custom-template",
                "name": "Custom Template",
                "subject": "Hi {{NAME}}",
                "body_html": "<p>Hello {{NAME}}</p>",
            },
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["slug"] == "custom-template"
        assert str(response.data["tenant"]) == str(tenant.id)

    def test_member_cannot_manage_templates(self, authenticated_client, user, tenant):
        Membership.objects.create(user=user, tenant=tenant, role="member")

        response = authenticated_client.get(
            "/api/v1/emails/templates/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestEmailTemplateDetail:
    def test_get_template(self, authenticated_client, user, tenant, system_template):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.get(
            f"/api/v1/emails/templates/{system_template.id}/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == "test-template"

    def test_patch_tenant_template(self, authenticated_client, user, tenant):
        Membership.objects.create(user=user, tenant=tenant, role="admin")
        tpl = EmailTemplate.objects.create(
            tenant=tenant, slug="editable", name="Editable",
            subject="Old Subject", body_html="<p>Old</p>",
        )

        response = authenticated_client.patch(
            f"/api/v1/emails/templates/{tpl.id}/",
            data={"subject": "New Subject"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["subject"] == "New Subject"

    def test_cannot_patch_system_template(self, authenticated_client, user, tenant, system_template):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.patch(
            f"/api/v1/emails/templates/{system_template.id}/",
            data={"subject": "Hacked"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_soft_deletes(self, authenticated_client, user, tenant):
        Membership.objects.create(user=user, tenant=tenant, role="admin")
        tpl = EmailTemplate.objects.create(
            tenant=tenant, slug="deletable", name="Deletable",
            subject="Subject", body_html="<p>Body</p>",
        )

        response = authenticated_client.delete(
            f"/api/v1/emails/templates/{tpl.id}/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        tpl.refresh_from_db()
        assert tpl.is_active is False


@pytest.mark.django_db
class TestEmailLogList:
    def test_list_logs(self, authenticated_client, user, tenant, system_template):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-log"
            from apps.emails.services import EmailService

            EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        response = authenticated_client.get(
            "/api/v1/emails/logs/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_filter_logs_by_status(self, authenticated_client, user, tenant, system_template):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-filter"
            from apps.emails.services import EmailService

            EmailService.send(
                tenant=tenant,
                template_slug="test-template",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        response = authenticated_client.get(
            "/api/v1/emails/logs/?status=pending",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        response = authenticated_client.get(
            "/api/v1/emails/logs/?status=sent",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert len(response.data["results"]) == 0


@pytest.mark.django_db
class TestSendEmailView:
    def test_send_email_via_api(self, authenticated_client, user, tenant, system_template, active_smtp_provider):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-api"

            response = authenticated_client.post(
                "/api/v1/emails/send/",
                data={
                    "template_slug": "test-template",
                    "recipient_email": "kunde@example.com",
                    "context": {"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
                },
                format="json",
                HTTP_X_TENANT_ID=str(tenant.id),
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["status"] == "pending"
        assert response.data["recipient_email"] == "kunde@example.com"

    def test_send_email_422_without_provider(self, authenticated_client, user, tenant, system_template):
        """No active provider → 422 with clear message."""
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.post(
            "/api/v1/emails/send/",
            data={
                "template_slug": "test-template",
                "recipient_email": "kunde@example.com",
                "context": {"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            },
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Kein E-Mail-Provider konfiguriert" in response.data["detail"]

    def test_send_email_404_for_missing_template(self, authenticated_client, user, tenant, active_smtp_provider):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.post(
            "/api/v1/emails/send/",
            data={
                "template_slug": "nonexistent",
                "recipient_email": "kunde@example.com",
            },
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestSequenceViews:
    def test_list_sequences(self, authenticated_client, user, tenant, system_sequence):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        response = authenticated_client.get(
            "/api/v1/emails/sequences/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_start_sequence(self, authenticated_client, user, tenant, system_sequence):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-start"

            response = authenticated_client.post(
                "/api/v1/emails/sequences/start/",
                data={
                    "sequence_slug": "test-sequence",
                    "recipient_email": "kunde@example.com",
                    "context": {"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
                },
                format="json",
                HTTP_X_TENANT_ID=str(tenant.id),
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "active"


@pytest.mark.django_db
class TestEnrollmentViews:
    def test_list_enrollments(self, authenticated_client, user, tenant, system_sequence):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-list"
            from apps.emails.services import EmailService

            EmailService.start_sequence(
                tenant=tenant,
                sequence_slug="test-sequence",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        response = authenticated_client.get(
            "/api/v1/emails/enrollments/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_cancel_enrollment(self, authenticated_client, user, tenant, system_sequence):
        Membership.objects.create(user=user, tenant=tenant, role="admin")

        with patch("apps.emails.tasks.send_email_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-cancel"
            from apps.emails.services import EmailService

            enrollment = EmailService.start_sequence(
                tenant=tenant,
                sequence_slug="test-sequence",
                recipient_email="kunde@example.com",
                context={"FIRST_NAME": "Max", "TENANT_NAME": "Agentur"},
            )

        response = authenticated_client.post(
            f"/api/v1/emails/enrollments/{enrollment.id}/cancel/",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "cancelled"
