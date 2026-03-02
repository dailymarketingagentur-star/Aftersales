import structlog
from django.core.management.base import BaseCommand

logger = structlog.get_logger()

# fmt: off
TEMPLATES = [
    {
        "slug": "search-jira-user",
        "name": "Jira-User suchen",
        "description": "Sucht einen Jira-User anhand der E-Mail-Adresse (fuer Lead-Account-ID).",
        "method": "GET",
        "endpoint": "/rest/api/3/user/search?query={{SEARCH_EMAIL}}",
        "body_json": {},
        "variables": ["SEARCH_EMAIL"],
        "output_mapping": {"0.accountId": "LEAD_ACCOUNT_ID"},
    },
    {
        "slug": "create-jira-project",
        "name": "Jira-Projekt erstellen",
        "description": "Erstellt ein neues Jira-Projekt mit Template, Lead und Beschreibung.",
        "method": "POST",
        "endpoint": "/rest/api/3/project",
        "body_json": {
            "key": "{{PROJECT_KEY}}",
            "name": "{{PROJECT_NAME}}",
            "projectTypeKey": "business",
            "projectTemplateKey": "{{PROJECT_TEMPLATE_KEY}}",
            "description": "{{PROJECT_DESCRIPTION}}",
            "leadAccountId": "{{LEAD_ACCOUNT_ID}}",
        },
        "variables": [
            "PROJECT_KEY", "PROJECT_NAME", "PROJECT_TEMPLATE_KEY",
            "PROJECT_DESCRIPTION", "LEAD_ACCOUNT_ID",
        ],
        "output_mapping": {"id": "PROJECT_ID", "key": "PROJECT_KEY_RESULT"},
    },
    {
        "slug": "assign-workflow-scheme",
        "name": "Workflow-Schema zuweisen",
        "description": "Weist dem Projekt ein Workflow-Schema zu.",
        "method": "PUT",
        "endpoint": "/rest/api/3/workflowscheme/project",
        "body_json": {
            "workflowSchemeId": "{{WORKFLOW_SCHEME_ID}}",
            "projectId": "{{PROJECT_ID}}",
        },
        "variables": ["WORKFLOW_SCHEME_ID", "PROJECT_ID"],
        "output_mapping": {},
    },
    {
        "slug": "assign-issue-type-screen-scheme",
        "name": "Issue-Type-Screen-Schema zuweisen",
        "description": "Weist dem Projekt ein Issue-Type-Screen-Schema zu.",
        "method": "PUT",
        "endpoint": "/rest/api/3/issuetypescreenscheme/project",
        "body_json": {
            "issueTypeScreenSchemeId": "{{ISSUE_TYPE_SCREEN_SCHEME_ID}}",
            "projectId": "{{PROJECT_ID}}",
        },
        "variables": ["ISSUE_TYPE_SCREEN_SCHEME_ID", "PROJECT_ID"],
        "output_mapping": {},
    },
    {
        "slug": "assign-field-config-scheme",
        "name": "Feldkonfigurations-Schema zuweisen",
        "description": "Weist dem Projekt ein Feldkonfigurations-Schema zu.",
        "method": "PUT",
        "endpoint": "/rest/api/3/fieldconfigurationscheme/project",
        "body_json": {
            "fieldConfigurationSchemeId": "{{FIELD_CONFIG_SCHEME_ID}}",
            "projectId": "{{PROJECT_ID}}",
        },
        "variables": ["FIELD_CONFIG_SCHEME_ID", "PROJECT_ID"],
        "output_mapping": {},
    },
    {
        "slug": "assign-issue-type-scheme",
        "name": "Issue-Type-Schema zuweisen",
        "description": "Weist dem Projekt ein Issue-Type-Schema zu.",
        "method": "PUT",
        "endpoint": "/rest/api/3/issuetypescheme/project",
        "body_json": {
            "issueTypeSchemeId": "{{ISSUE_TYPE_SCHEME_ID}}",
            "projectId": "{{PROJECT_ID}}",
        },
        "variables": ["ISSUE_TYPE_SCHEME_ID", "PROJECT_ID"],
        "output_mapping": {},
    },
    {
        "slug": "create-jira-issue",
        "name": "Jira-Issue erstellen",
        "description": "Erstellt ein Issue mit Custom Fields (E-Mail, Firma, Telefon, Website).",
        "method": "POST",
        "endpoint": "/rest/api/3/issue",
        "body_json": {
            "fields": {
                "project": {"id": "{{PROJECT_ID}}"},
                "summary": "{{ISSUE_SUMMARY}}",
                "issuetype": {"id": "{{ISSUE_TYPE_ID}}"},
                "{{CUSTOM_FIELD_EMAIL}}": "{{CONTACT_EMAIL}}",
                "{{CUSTOM_FIELD_COMPANY}}": "{{COMPANY_NAME}}",
                "{{CUSTOM_FIELD_PHONE}}": "{{CONTACT_PHONE}}",
                "{{CUSTOM_FIELD_WEBSITE}}": "{{WEBSITE_URL}}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "{{ISSUE_DESCRIPTION}}"}
                            ],
                        }
                    ],
                },
            }
        },
        "variables": [
            "PROJECT_ID", "ISSUE_SUMMARY", "ISSUE_TYPE_ID",
            "CUSTOM_FIELD_EMAIL", "CONTACT_EMAIL",
            "CUSTOM_FIELD_COMPANY", "COMPANY_NAME",
            "CUSTOM_FIELD_PHONE", "CONTACT_PHONE",
            "CUSTOM_FIELD_WEBSITE", "WEBSITE_URL",
            "ISSUE_DESCRIPTION",
        ],
        "output_mapping": {"id": "ISSUE_ID", "key": "ISSUE_KEY"},
    },
    {
        "slug": "update-jira-issue",
        "name": "Jira-Issue aktualisieren",
        "description": "Aktualisiert ein bestehendes Jira-Issue (Label hinzufuegen).",
        "method": "PUT",
        "endpoint": "/rest/api/3/issue/{{ISSUE_KEY}}",
        "body_json": {
            "update": {
                "labels": [{"add": "{{LABEL}}"}],
            }
        },
        "variables": ["ISSUE_KEY", "LABEL"],
        "output_mapping": {},
    },
]

SEQUENCES = [
    {
        "slug": "client-onboarding",
        "name": "Client-Onboarding in Jira",
        "description": (
            "Vollstaendiges Jira-Onboarding: User suchen, Projekt erstellen, "
            "4 Schema-Zuweisungen, Issue erstellen, Label setzen."
        ),
        "steps": [
            {"template_slug": "search-jira-user",                "position": 1, "delay_seconds": 0},
            {"template_slug": "create-jira-project",             "position": 2, "delay_seconds": 2},
            {"template_slug": "assign-workflow-scheme",           "position": 3, "delay_seconds": 1},
            {"template_slug": "assign-issue-type-screen-scheme",  "position": 4, "delay_seconds": 1},
            {"template_slug": "assign-field-config-scheme",       "position": 5, "delay_seconds": 1},
            {"template_slug": "assign-issue-type-scheme",         "position": 6, "delay_seconds": 1},
            {"template_slug": "create-jira-issue",               "position": 7, "delay_seconds": 2},
            {"template_slug": "update-jira-issue",               "position": 8, "delay_seconds": 1},
        ],
    },
]
# fmt: on


class Command(BaseCommand):
    help = "Seed system-default Jira action templates and sequences (tenant=NULL)."

    def handle(self, *args, **options):
        from apps.integrations.models import ActionSequence, ActionTemplate, SequenceStep

        created_templates = 0
        updated_templates = 0

        for tpl_data in TEMPLATES:
            tpl, created = ActionTemplate.objects.update_or_create(
                tenant=None,
                slug=tpl_data["slug"],
                defaults={
                    "name": tpl_data["name"],
                    "description": tpl_data["description"],
                    "method": tpl_data["method"],
                    "endpoint": tpl_data["endpoint"],
                    "body_json": tpl_data["body_json"],
                    "variables": tpl_data["variables"],
                    "output_mapping": tpl_data["output_mapping"],
                    "is_active": True,
                    "is_system": True,
                },
            )
            if created:
                created_templates += 1
            else:
                updated_templates += 1

        self.stdout.write(f"Templates: {created_templates} created, {updated_templates} updated.")

        created_sequences = 0
        for seq_data in SEQUENCES:
            seq, created = ActionSequence.objects.update_or_create(
                tenant=None,
                slug=seq_data["slug"],
                defaults={
                    "name": seq_data["name"],
                    "description": seq_data["description"],
                    "is_active": True,
                },
            )
            if created:
                created_sequences += 1

            # Remove old steps that are no longer in the definition
            defined_positions = {s["position"] for s in seq_data["steps"]}
            SequenceStep.objects.filter(sequence=seq).exclude(position__in=defined_positions).delete()

            for step_data in seq_data["steps"]:
                template = ActionTemplate.objects.get(
                    tenant=None, slug=step_data["template_slug"],
                )
                SequenceStep.objects.update_or_create(
                    sequence=seq,
                    position=step_data["position"],
                    defaults={
                        "template": template,
                        "delay_seconds": step_data["delay_seconds"],
                        "is_active": True,
                    },
                )

        self.stdout.write(f"Sequences: {created_sequences} created.")
        self.stdout.write(self.style.SUCCESS("Jira seed data loaded successfully."))
