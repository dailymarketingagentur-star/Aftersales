import structlog
from django.core.management.base import BaseCommand

logger = structlog.get_logger()

# fmt: off
TEMPLATES = [
    {
        "slug": "find-confluence-space",
        "name": "Confluence-Space suchen",
        "description": "Sucht einen Confluence-Space anhand des Space-Keys.",
        "method": "GET",
        "endpoint": "/wiki/api/v2/spaces?keys={{SPACE_KEY}}",
        "body_json": {},
        "variables": ["SPACE_KEY"],
        "output_mapping": {"results.0.id": "SPACE_ID"},
    },
    {
        "slug": "create-confluence-page",
        "name": "Confluence-Seite erstellen",
        "description": "Erstellt eine neue Confluence-Seite in einem Space.",
        "method": "POST",
        "endpoint": "/wiki/api/v2/pages",
        "body_json": {
            "spaceId": "{{SPACE_ID}}",
            "status": "current",
            "title": "{{PAGE_TITLE}}",
            "body": {
                "representation": "storage",
                "value": "{{PAGE_BODY}}",
            },
        },
        "variables": ["SPACE_ID", "PAGE_TITLE", "PAGE_BODY"],
        "output_mapping": {"id": "PAGE_ID"},
    },
    {
        "slug": "update-confluence-page",
        "name": "Confluence-Seite aktualisieren",
        "description": "Aktualisiert eine bestehende Confluence-Seite (mit Versionsnummer).",
        "method": "PUT",
        "endpoint": "/wiki/api/v2/pages/{{PAGE_ID}}",
        "body_json": {
            "id": "{{PAGE_ID}}",
            "status": "current",
            "title": "{{PAGE_TITLE}}",
            "body": {
                "representation": "storage",
                "value": "{{PAGE_BODY}}",
            },
            "version": {
                "number": "{{VERSION_NUMBER}}",
            },
        },
        "variables": ["PAGE_ID", "PAGE_TITLE", "PAGE_BODY", "VERSION_NUMBER"],
        "output_mapping": {"id": "PAGE_ID_RESULT", "version.number": "NEW_VERSION"},
    },
]

SEQUENCES = [
    {
        "slug": "create-client-confluence-page",
        "name": "Client-Confluence-Seite erstellen",
        "description": "Space suchen und dann Confluence-Seite fuer den Mandanten erstellen.",
        "steps": [
            {"template_slug": "find-confluence-space", "position": 1, "delay_seconds": 0},
            {"template_slug": "create-confluence-page", "position": 2, "delay_seconds": 1},
        ],
    },
]
# fmt: on


class Command(BaseCommand):
    help = "Seed system-default Confluence action templates and sequences (tenant=NULL)."

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
                    "target_type": "jira",
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
        self.stdout.write(self.style.SUCCESS("Confluence seed data loaded successfully."))
