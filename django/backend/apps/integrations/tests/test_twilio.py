from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status

from apps.integrations.models import TwilioConnection
from apps.users.models import Membership

VALID_ACCOUNT_SID = "AC" + "a" * 32
VALID_TWIML_APP_SID = "AP" + "b" * 32
VALID_PHONE = "+4930123456"


@pytest.fixture
def owner_tenant(user, tenant_factory):
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="owner")
    return tenant


@pytest.fixture
def member_tenant(user_factory, tenant_factory):
    """Tenant with user as member (not owner)."""
    member = user_factory(email="member@test.com")
    tenant = tenant_factory()
    Membership.objects.create(user=member, tenant=tenant, role="member")
    return {"user": member, "tenant": tenant}


@pytest.fixture
def twilio_conn(owner_tenant):
    conn = TwilioConnection(
        tenant=owner_tenant,
        label="Test Twilio",
        account_sid=VALID_ACCOUNT_SID,
        twiml_app_sid=VALID_TWIML_APP_SID,
        phone_number=VALID_PHONE,
    )
    conn.set_auth_token("test-auth-token-123")
    conn.save()
    return conn


# ---------------------------------------------------------------------------
# CRUD Tests (Owner only)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestTwilioConnectionCRUD:
    def test_get_no_connection(self, authenticated_client, owner_tenant):
        resp = authenticated_client.get(
            "/api/v1/integrations/twilio/connection/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_put_creates_connection(self, authenticated_client, owner_tenant):
        resp = authenticated_client.put(
            "/api/v1/integrations/twilio/connection/",
            {
                "account_sid": VALID_ACCOUNT_SID,
                "auth_token": "my-secret-token",
                "twiml_app_sid": VALID_TWIML_APP_SID,
                "phone_number": VALID_PHONE,
            },
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["account_sid"] == VALID_ACCOUNT_SID
        assert resp.data["phone_number"] == VALID_PHONE
        # Token should NOT be in response
        assert "auth_token" not in resp.data
        assert "auth_token_encrypted" not in resp.data

    def test_put_updates_existing(self, authenticated_client, owner_tenant, twilio_conn):
        resp = authenticated_client.put(
            "/api/v1/integrations/twilio/connection/",
            {
                "account_sid": VALID_ACCOUNT_SID,
                "auth_token": "new-token",
                "twiml_app_sid": VALID_TWIML_APP_SID,
                "phone_number": "+491234567890",
            },
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["phone_number"] == "+491234567890"

    def test_get_existing_connection(self, authenticated_client, owner_tenant, twilio_conn):
        resp = authenticated_client.get(
            "/api/v1/integrations/twilio/connection/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["account_sid"] == VALID_ACCOUNT_SID

    def test_delete_connection(self, authenticated_client, owner_tenant, twilio_conn):
        resp = authenticated_client.delete(
            "/api/v1/integrations/twilio/connection/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        # Verify it's deactivated, not deleted
        assert TwilioConnection.objects.filter(tenant=owner_tenant, is_active=False).exists()

    def test_delete_no_connection(self, authenticated_client, owner_tenant):
        resp = authenticated_client.delete(
            "/api/v1/integrations/twilio/connection/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestTwilioValidation:
    def test_invalid_account_sid(self, authenticated_client, owner_tenant):
        resp = authenticated_client.put(
            "/api/v1/integrations/twilio/connection/",
            {
                "account_sid": "INVALID",
                "auth_token": "token",
                "twiml_app_sid": VALID_TWIML_APP_SID,
                "phone_number": VALID_PHONE,
            },
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_twiml_app_sid(self, authenticated_client, owner_tenant):
        resp = authenticated_client.put(
            "/api/v1/integrations/twilio/connection/",
            {
                "account_sid": VALID_ACCOUNT_SID,
                "auth_token": "token",
                "twiml_app_sid": "INVALID",
                "phone_number": VALID_PHONE,
            },
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_phone_number(self, authenticated_client, owner_tenant):
        resp = authenticated_client.put(
            "/api/v1/integrations/twilio/connection/",
            {
                "account_sid": VALID_ACCOUNT_SID,
                "auth_token": "token",
                "twiml_app_sid": VALID_TWIML_APP_SID,
                "phone_number": "0301234",  # no E.164 format
            },
            format="json",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Token Endpoint
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestTwilioToken:
    def test_token_no_connection(self, authenticated_client, owner_tenant):
        """Token endpoint returns 404 when no connection exists."""
        resp = authenticated_client.post(
            "/api/v1/integrations/twilio/token/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_token_with_connection(self, authenticated_client, owner_tenant, twilio_conn):
        """Token endpoint returns 200 with a JWT when connection exists (or 500 if twilio not installed)."""
        mock_token = MagicMock()
        mock_token.to_jwt.return_value = "fake-jwt-token"

        mock_grant = MagicMock()

        with patch("twilio.jwt.access_token.AccessToken", return_value=mock_token), \
             patch("twilio.jwt.access_token.grants.VoiceGrant", return_value=mock_grant):
            resp = authenticated_client.post(
                "/api/v1/integrations/twilio/token/",
                HTTP_X_TENANT_ID=str(owner_tenant.id),
            )

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["token"] == "fake-jwt-token"
        assert resp.data["phone_number"] == twilio_conn.phone_number

    def test_member_can_get_token(self, api_client, member_tenant, owner_tenant, twilio_conn):
        """Members (not just owners) can get access tokens."""
        # Create a member on the same tenant that has the twilio connection
        from apps.users.models import User

        member = User.objects.create_user(email="member2@test.com", password="testpass123")
        Membership.objects.create(user=member, tenant=owner_tenant, role="member")
        api_client.force_authenticate(user=member)

        resp = api_client.post(
            "/api/v1/integrations/twilio/token/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        # Should get 200 or 500 (if twilio lib not installed), not 403
        assert resp.status_code != status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# TwiML Webhook
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestTwiMLWebhook:
    def test_twiml_returns_xml(self, api_client):
        """TwiML endpoint returns valid XML with dial instruction."""
        resp = api_client.post(
            "/api/v1/integrations/twilio/twiml/voice/",
            {"To": "+4930123456", "CallerId": "+4930654321"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp["Content-Type"] == "application/xml"
        content = resp.content.decode()
        assert "<Dial" in content
        assert "+4930123456" in content

    def test_twiml_no_to_number(self, api_client):
        """TwiML endpoint returns error message when no To number given."""
        resp = api_client.post(
            "/api/v1/integrations/twilio/twiml/voice/",
            {},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp["Content-Type"] == "application/xml"
        content = resp.content.decode()
        assert "<Say" in content

    def test_twiml_no_auth_required(self, api_client):
        """TwiML endpoint is public — no auth needed."""
        # api_client is NOT authenticated here
        resp = api_client.post(
            "/api/v1/integrations/twilio/twiml/voice/",
            {"To": "+4930123456", "CallerId": "+4930654321"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_twiml_no_tenant_header_required(self, api_client):
        """TwiML endpoint doesn't need X-Tenant-ID header."""
        resp = api_client.post(
            "/api/v1/integrations/twilio/twiml/voice/",
            {"To": "+4930123456"},
            format="json",
        )
        # Should NOT get 400 "X-Tenant-ID header is required"
        assert resp.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# Permission Tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestTwilioPermissions:
    def test_member_cannot_crud(self, api_client, member_tenant):
        """Members cannot create/update/delete Twilio connections."""
        api_client.force_authenticate(user=member_tenant["user"])
        tenant_id = str(member_tenant["tenant"].id)

        resp = api_client.put(
            "/api/v1/integrations/twilio/connection/",
            {
                "account_sid": VALID_ACCOUNT_SID,
                "auth_token": "token",
                "twiml_app_sid": VALID_TWIML_APP_SID,
                "phone_number": VALID_PHONE,
            },
            format="json",
            HTTP_X_TENANT_ID=tenant_id,
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_member_cannot_delete(self, api_client, member_tenant):
        api_client.force_authenticate(user=member_tenant["user"])
        resp = api_client.delete(
            "/api/v1/integrations/twilio/connection/",
            HTTP_X_TENANT_ID=str(member_tenant["tenant"].id),
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_member_cannot_test_connection(self, api_client, member_tenant):
        api_client.force_authenticate(user=member_tenant["user"])
        resp = api_client.post(
            "/api/v1/integrations/twilio/connection/test/",
            HTTP_X_TENANT_ID=str(member_tenant["tenant"].id),
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_access(self, api_client, owner_tenant):
        """Unauthenticated requests are rejected."""
        resp = api_client.get(
            "/api/v1/integrations/twilio/connection/",
            HTTP_X_TENANT_ID=str(owner_tenant.id),
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ---------------------------------------------------------------------------
# Model Tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestTwilioConnectionModel:
    def test_encrypt_decrypt_token(self, owner_tenant):
        conn = TwilioConnection(
            tenant=owner_tenant,
            account_sid=VALID_ACCOUNT_SID,
            twiml_app_sid=VALID_TWIML_APP_SID,
            phone_number=VALID_PHONE,
        )
        conn.set_auth_token("super-secret-token")
        assert conn.auth_token_encrypted != "super-secret-token"
        assert conn.get_auth_token() == "super-secret-token"

    def test_str_representation(self, twilio_conn):
        assert "Test Twilio" in str(twilio_conn)
