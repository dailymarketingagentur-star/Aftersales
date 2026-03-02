import pytest
from django.core.management import call_command

from apps.integrations.models import ActionSequence, ActionTemplate, SequenceStep


@pytest.mark.django_db
class TestSeedConfluenceTemplates:
    def test_creates_3_templates(self):
        call_command("seed_confluence_templates")
        templates = ActionTemplate.objects.filter(
            tenant__isnull=True, is_system=True, slug__startswith="find-confluence"
        ) | ActionTemplate.objects.filter(
            tenant__isnull=True, is_system=True, slug__startswith="create-confluence"
        ) | ActionTemplate.objects.filter(
            tenant__isnull=True, is_system=True, slug__startswith="update-confluence"
        )
        assert templates.count() == 3

    def test_expected_slugs(self):
        call_command("seed_confluence_templates")
        slugs = set(
            ActionTemplate.objects.filter(
                tenant__isnull=True, slug__in=[
                    "find-confluence-space",
                    "create-confluence-page",
                    "update-confluence-page",
                ]
            ).values_list("slug", flat=True)
        )
        assert slugs == {
            "find-confluence-space",
            "create-confluence-page",
            "update-confluence-page",
        }

    def test_creates_sequence_with_2_steps(self):
        call_command("seed_confluence_templates")
        seq = ActionSequence.objects.get(tenant__isnull=True, slug="create-client-confluence-page")
        steps = seq.steps.filter(is_active=True).order_by("position")
        assert steps.count() == 2
        slugs = list(steps.values_list("template__slug", flat=True))
        assert slugs == ["find-confluence-space", "create-confluence-page"]

    def test_templates_have_target_type_jira(self):
        """Confluence templates use target_type=jira for shared Atlassian credentials."""
        call_command("seed_confluence_templates")
        for slug in ["find-confluence-space", "create-confluence-page", "update-confluence-page"]:
            tpl = ActionTemplate.objects.get(tenant__isnull=True, slug=slug)
            assert tpl.target_type == "jira"

    def test_idempotency(self):
        """Running seed twice should not create duplicates."""
        call_command("seed_confluence_templates")
        call_command("seed_confluence_templates")

        confluence_slugs = ["find-confluence-space", "create-confluence-page", "update-confluence-page"]
        for slug in confluence_slugs:
            assert ActionTemplate.objects.filter(tenant__isnull=True, slug=slug).count() == 1

        assert ActionSequence.objects.filter(
            tenant__isnull=True, slug="create-client-confluence-page"
        ).count() == 1

    def test_output_mappings(self):
        call_command("seed_confluence_templates")

        tpl = ActionTemplate.objects.get(tenant__isnull=True, slug="find-confluence-space")
        assert tpl.output_mapping == {"results.0.id": "SPACE_ID"}

        tpl = ActionTemplate.objects.get(tenant__isnull=True, slug="create-confluence-page")
        assert tpl.output_mapping == {"id": "PAGE_ID"}

        tpl = ActionTemplate.objects.get(tenant__isnull=True, slug="update-confluence-page")
        assert "PAGE_ID_RESULT" in tpl.output_mapping.values()
        assert "NEW_VERSION" in tpl.output_mapping.values()
