"""
Field Registry fuer Integrationstypen.

Definiert alle verfuegbaren Integrationen und ihre mandantenspezifischen Felder.
Neue Integrationen hinzufuegen = nur hier aendern, keine Migration noetig.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IntegrationField:
    """Ein einzelnes Feld einer Integration."""

    key: str
    label: str  # Deutsch mit echten Umlauten
    field_type: str  # "url" oder "text"


@dataclass(frozen=True)
class IntegrationTypeDef:
    """Definition eines Integrationstyps mit seinen Feldern."""

    key: str
    label: str  # Deutsch mit echten Umlauten
    description: str
    icon: str  # Wird im Frontend als Bezeichner verwendet
    fields: list[IntegrationField] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Registry — alle Integrationstypen und ihre Felder
# ---------------------------------------------------------------------------
INTEGRATION_TYPES: dict[str, IntegrationTypeDef] = {}


def _register(*types: IntegrationTypeDef) -> None:
    for t in types:
        INTEGRATION_TYPES[t.key] = t


_register(
    IntegrationTypeDef(
        key="jira",
        label="Jira",
        description="Projekte und Issues in Jira Cloud verwalten",
        icon="jira",
        fields=[
            IntegrationField(key="project_url", label="Link zum Jira-Projekt", field_type="url"),
            IntegrationField(key="project_key", label="Projekt-Key", field_type="text"),
            IntegrationField(key="project_id", label="Projekt-ID", field_type="text"),
        ],
    ),
    IntegrationTypeDef(
        key="hubspot",
        label="HubSpot",
        description="CRM-Kontakte und Deals verwalten",
        icon="hubspot",
        fields=[
            IntegrationField(key="company_url", label="Link zum HubSpot-Unternehmen", field_type="url"),
            IntegrationField(key="company_id", label="Unternehmens-ID", field_type="text"),
            IntegrationField(key="deal_url", label="Link zum Deal", field_type="url"),
            IntegrationField(key="deal_id", label="Deal-ID", field_type="text"),
        ],
    ),
    IntegrationTypeDef(
        key="clickup",
        label="ClickUp",
        description="Aufgaben und Projekte in ClickUp verwalten",
        icon="clickup",
        fields=[
            IntegrationField(key="space_url", label="Link zum Space", field_type="url"),
            IntegrationField(key="space_id", label="Space-ID", field_type="text"),
            IntegrationField(key="folder_id", label="Ordner-ID", field_type="text"),
        ],
    ),
    IntegrationTypeDef(
        key="slack",
        label="Slack",
        description="Benachrichtigungen und Updates per Slack",
        icon="slack",
        fields=[
            IntegrationField(key="channel_name", label="Kanal-Name", field_type="text"),
            IntegrationField(key="channel_id", label="Kanal-ID", field_type="text"),
            IntegrationField(key="webhook_url", label="Webhook-URL", field_type="url"),
        ],
    ),
    IntegrationTypeDef(
        key="activecampaign",
        label="ActiveCampaign",
        description="E-Mail-Marketing und Automationen",
        icon="activecampaign",
        fields=[
            IntegrationField(key="contact_url", label="Link zum Kontakt", field_type="url"),
            IntegrationField(key="contact_id", label="Kontakt-ID", field_type="text"),
            IntegrationField(key="list_id", label="Listen-ID", field_type="text"),
        ],
    ),
    IntegrationTypeDef(
        key="agencyanalytics",
        label="AgencyAnalytics",
        description="Reporting und Kampagnen-Tracking",
        icon="agencyanalytics",
        fields=[
            IntegrationField(key="campaign_url", label="Link zur Kampagne", field_type="url"),
            IntegrationField(key="campaign_id", label="Kampagnen-ID", field_type="text"),
        ],
    ),
    IntegrationTypeDef(
        key="calendly",
        label="Calendly",
        description="Terminbuchung und Kalender-Integration",
        icon="calendly",
        fields=[
            IntegrationField(key="scheduling_url", label="Buchungs-URL", field_type="url"),
        ],
    ),
    IntegrationTypeDef(
        key="twilio",
        label="Twilio Telefonie",
        description="Browser-basierte Telefonie direkt aus der Plattform",
        icon="twilio",
        fields=[],
    ),
    IntegrationTypeDef(
        key="confluence",
        label="Confluence",
        description="Dokumentation und Wissensdatenbank in Confluence Cloud",
        icon="confluence",
        fields=[
            IntegrationField(key="space_key", label="Confluence Space-Key", field_type="text"),
            IntegrationField(key="page_url", label="Link zur Confluence-Seite", field_type="url"),
            IntegrationField(key="page_id", label="Seiten-ID", field_type="text"),
        ],
    ),
    IntegrationTypeDef(
        key="webhook",
        label="Webhooks",
        description="Benutzerdefinierte HTTP-Aufrufe an externe Systeme",
        icon="webhook",
        fields=[],
    ),
)


def get_valid_keys() -> set[str]:
    """Alle gueltigen Integrationstyp-Keys."""
    return set(INTEGRATION_TYPES.keys())


def get_field_keys(integration_type: str) -> set[str]:
    """Alle gueltigen Feld-Keys fuer einen Integrationstyp."""
    typedef = INTEGRATION_TYPES.get(integration_type)
    if not typedef:
        return set()
    return {f.key for f in typedef.fields}
