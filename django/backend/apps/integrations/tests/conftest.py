import pytest

from apps.emails.models import EmailProviderConnection
from apps.integrations.models import (
    ActionExecution,
    ActionSequence,
    ActionTemplate,
    JiraConnection,
    SequenceStep,
    TwilioConnection,
)
from apps.users.models import Membership


@pytest.fixture
def owner_setup(user, tenant_factory):
    """Tenant with user as owner + active subscription."""
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="owner")
    return tenant


@pytest.fixture
def admin_setup(user, tenant_factory):
    """Tenant with user as admin + active subscription."""
    tenant = tenant_factory()
    Membership.objects.create(user=user, tenant=tenant, role="admin")
    return tenant


@pytest.fixture
def jira_connection(owner_setup):
    """Active Jira connection for the tenant."""
    conn = JiraConnection(
        tenant=owner_setup,
        label="Test Jira",
        jira_url="https://test.atlassian.net",
        jira_email="test@example.com",
    )
    conn.set_token("test-api-token-123")
    conn.save()
    return conn


@pytest.fixture
def twilio_connection(owner_setup):
    """Active Twilio connection for the tenant."""
    conn = TwilioConnection(
        tenant=owner_setup,
        label="Test Twilio",
        account_sid="AC" + "a" * 32,
        twiml_app_sid="AP" + "b" * 32,
        phone_number="+4930123456",
    )
    conn.set_auth_token("test-auth-token-123")
    conn.save()
    return conn


@pytest.fixture
def member_setup(user_factory, tenant_factory):
    """Tenant with a separate user as member + active subscription."""
    member_user = user_factory(email="member@example.com")
    tenant = tenant_factory()
    Membership.objects.create(user=member_user, tenant=tenant, role="member")
    return {"user": member_user, "tenant": tenant}


@pytest.fixture
def system_template():
    """System-level action template (tenant=NULL)."""
    return ActionTemplate.objects.create(
        tenant=None,
        slug="create-jira-issue",
        name="Jira-Issue erstellen",
        method="POST",
        endpoint="/rest/api/3/issue",
        body_json={
            "fields": {
                "project": {"key": "{{PROJECT_KEY}}"},
                "summary": "{{ISSUE_SUMMARY}}",
                "issuetype": {"name": "Task"},
            }
        },
        variables=["PROJECT_KEY", "ISSUE_SUMMARY"],
        output_mapping={"id": "ISSUE_ID", "key": "ISSUE_KEY"},
        is_system=True,
    )


@pytest.fixture
def system_sequence(system_template):
    """System-level sequence with one step."""
    seq = ActionSequence.objects.create(
        tenant=None,
        slug="test-sequence",
        name="Test Sequence",
    )
    SequenceStep.objects.create(
        sequence=seq,
        template=system_template,
        position=1,
        delay_seconds=0,
    )
    return seq


@pytest.fixture
def source_target_setup(user, tenant_factory):
    """Two tenants owned by the same user. Source has SMTP, Jira, and ActionTemplate."""
    source = tenant_factory(name="Source Tenant", slug="source-tenant")
    target = tenant_factory(name="Target Tenant", slug="target-tenant")
    Membership.objects.create(user=user, tenant=source, role="owner")
    Membership.objects.create(user=user, tenant=target, role="owner")

    # SMTP provider with password
    smtp = EmailProviderConnection(
        tenant=source,
        provider_type="smtp",
        label="Source SMTP",
        smtp_host="mail.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_use_tls=True,
        from_email="noreply@example.com",
        from_name="Source",
    )
    smtp.set_smtp_password("smtp-secret-123")
    smtp.save()

    # Jira connection with token
    jira = JiraConnection(
        tenant=source,
        label="Source Jira",
        jira_url="https://source.atlassian.net",
        jira_email="jira@example.com",
    )
    jira.set_token("jira-token-456")
    jira.save()

    # Tenant-specific action template
    ActionTemplate.objects.create(
        tenant=source,
        slug="custom-action",
        name="Custom Action",
        description="A custom action template",
        method="POST",
        endpoint="/rest/api/3/issue",
        body_json={"fields": {"summary": "{{SUMMARY}}"}},
        variables=["SUMMARY"],
        is_system=False,
    )

    return {"user": user, "source": source, "target": target}
