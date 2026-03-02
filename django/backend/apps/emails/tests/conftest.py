import pytest

from apps.emails.models import (
    EmailSequence,
    EmailTemplate,
    SequenceStep,
)


@pytest.fixture
def system_template(db):
    """System-default email template (tenant=NULL)."""
    return EmailTemplate.objects.create(
        tenant=None,
        slug="test-template",
        name="Test Template",
        subject="Hallo {{FIRST_NAME}}!",
        body_html="<p>Willkommen, {{FIRST_NAME}} bei {{TENANT_NAME}}.</p>",
        variables=["FIRST_NAME", "TENANT_NAME"],
    )


@pytest.fixture
def tenant_template(tenant):
    """Tenant-specific template that overrides the system default."""
    return EmailTemplate.objects.create(
        tenant=tenant,
        slug="test-template",
        name="Tenant Test Template",
        subject="Hey {{FIRST_NAME}} — Custom!",
        body_html="<p>Custom: {{FIRST_NAME}} bei {{TENANT_NAME}}.</p>",
        variables=["FIRST_NAME", "TENANT_NAME"],
    )


@pytest.fixture
def invite_template(db):
    """System team-invite template."""
    return EmailTemplate.objects.create(
        tenant=None,
        slug="team-invite",
        name="Team-Einladung",
        subject="Einladung zu {{TENANT_NAME}}",
        body_html=(
            "<p><strong>{{INVITED_BY}}</strong> hat Sie eingeladen, "
            "der Organisation <strong>{{TENANT_NAME}}</strong> beizutreten.</p>"
            '<p><a href="{{INVITE_URL}}">Einladung annehmen</a></p>'
        ),
        variables=["INVITED_BY", "TENANT_NAME", "INVITE_URL"],
    )


@pytest.fixture
def system_sequence(db, system_template):
    """System-default sequence with one step."""
    seq = EmailSequence.objects.create(
        tenant=None,
        slug="test-sequence",
        name="Test Sequence",
    )
    SequenceStep.objects.create(
        sequence=seq,
        template=system_template,
        position=1,
        delay_days=0,
        delay_hours=0,
    )
    return seq


@pytest.fixture
def multi_step_sequence(db):
    """System sequence with multiple steps at different delays."""
    tpl1 = EmailTemplate.objects.create(
        tenant=None,
        slug="seq-step-1",
        name="Step 1",
        subject="Step 1: {{FIRST_NAME}}",
        body_html="<p>Step 1</p>",
    )
    tpl2 = EmailTemplate.objects.create(
        tenant=None,
        slug="seq-step-2",
        name="Step 2",
        subject="Step 2: {{FIRST_NAME}}",
        body_html="<p>Step 2</p>",
    )
    seq = EmailSequence.objects.create(
        tenant=None,
        slug="multi-step-sequence",
        name="Multi-Step Sequence",
    )
    SequenceStep.objects.create(
        sequence=seq, template=tpl1, position=1,
        delay_days=0, delay_hours=0,
    )
    SequenceStep.objects.create(
        sequence=seq, template=tpl2, position=2,
        delay_days=3, delay_hours=0,
    )
    return seq
