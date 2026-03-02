import pytest
from django.core.management import call_command

from apps.integrations.models import ActionSequence, ActionTemplate, SequenceStep


@pytest.mark.django_db
class TestSeedJiraTemplates:
    def test_creates_8_templates(self):
        call_command("seed_jira_templates")
        templates = ActionTemplate.objects.filter(tenant__isnull=True, is_system=True)
        assert templates.count() == 8

    def test_expected_slugs(self):
        call_command("seed_jira_templates")
        slugs = set(
            ActionTemplate.objects.filter(tenant__isnull=True)
            .values_list("slug", flat=True)
        )
        expected = {
            "search-jira-user",
            "create-jira-project",
            "assign-workflow-scheme",
            "assign-issue-type-screen-scheme",
            "assign-field-config-scheme",
            "assign-issue-type-scheme",
            "create-jira-issue",
            "update-jira-issue",
        }
        assert slugs == expected

    def test_creates_sequence_with_8_steps(self):
        call_command("seed_jira_templates")
        seq = ActionSequence.objects.get(tenant__isnull=True, slug="client-onboarding")
        steps = seq.steps.filter(is_active=True).order_by("position")
        assert steps.count() == 8
        assert list(steps.values_list("position", flat=True)) == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_sequence_step_order(self):
        call_command("seed_jira_templates")
        seq = ActionSequence.objects.get(tenant__isnull=True, slug="client-onboarding")
        slugs = list(
            seq.steps.filter(is_active=True)
            .order_by("position")
            .values_list("template__slug", flat=True)
        )
        assert slugs == [
            "search-jira-user",
            "create-jira-project",
            "assign-workflow-scheme",
            "assign-issue-type-screen-scheme",
            "assign-field-config-scheme",
            "assign-issue-type-scheme",
            "create-jira-issue",
            "update-jira-issue",
        ]

    def test_output_mappings(self):
        call_command("seed_jira_templates")
        # search-jira-user should extract LEAD_ACCOUNT_ID from array response
        tpl = ActionTemplate.objects.get(tenant__isnull=True, slug="search-jira-user")
        assert tpl.output_mapping == {"0.accountId": "LEAD_ACCOUNT_ID"}

        # create-jira-project should extract PROJECT_ID
        tpl = ActionTemplate.objects.get(tenant__isnull=True, slug="create-jira-project")
        assert "PROJECT_ID" in tpl.output_mapping.values()

        # create-jira-issue should extract ISSUE_KEY
        tpl = ActionTemplate.objects.get(tenant__isnull=True, slug="create-jira-issue")
        assert "ISSUE_KEY" in tpl.output_mapping.values()

    def test_idempotency(self):
        """Running seed twice should not create duplicates."""
        call_command("seed_jira_templates")
        call_command("seed_jira_templates")

        assert ActionTemplate.objects.filter(tenant__isnull=True, is_system=True).count() == 8
        assert ActionSequence.objects.filter(tenant__isnull=True, slug="client-onboarding").count() == 1
        assert SequenceStep.objects.filter(
            sequence__slug="client-onboarding", sequence__tenant__isnull=True
        ).count() == 8

    def test_create_jira_issue_has_custom_field_placeholders(self):
        """create-jira-issue template should have {{CUSTOM_FIELD_*}} keys in body."""
        call_command("seed_jira_templates")
        tpl = ActionTemplate.objects.get(tenant__isnull=True, slug="create-jira-issue")
        fields = tpl.body_json.get("fields", {})
        # Keys should contain placeholders like {{CUSTOM_FIELD_EMAIL}}
        keys = set(fields.keys())
        assert "{{CUSTOM_FIELD_EMAIL}}" in keys
        assert "{{CUSTOM_FIELD_COMPANY}}" in keys
        assert "{{CUSTOM_FIELD_PHONE}}" in keys
        assert "{{CUSTOM_FIELD_WEBSITE}}" in keys

    def test_template_methods(self):
        """Each template should have the correct HTTP method."""
        call_command("seed_jira_templates")
        expected_methods = {
            "search-jira-user": "GET",
            "create-jira-project": "POST",
            "assign-workflow-scheme": "PUT",
            "assign-issue-type-screen-scheme": "PUT",
            "assign-field-config-scheme": "PUT",
            "assign-issue-type-scheme": "PUT",
            "create-jira-issue": "POST",
            "update-jira-issue": "PUT",
        }
        for slug, method in expected_methods.items():
            tpl = ActionTemplate.objects.get(tenant__isnull=True, slug=slug)
            assert tpl.method == method, f"{slug} should be {method}, got {tpl.method}"
