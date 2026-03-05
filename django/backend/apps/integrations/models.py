import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TenantScopedModel, TimestampedModel
from django.core.validators import RegexValidator

from apps.integrations.encryption import decrypt_token, encrypt_token
from apps.integrations.registry import get_valid_keys


# ---------------------------------------------------------------------------
# JiraConnection — one active connection per tenant
# ---------------------------------------------------------------------------
class JiraConnection(TenantScopedModel):
    """Per-tenant Jira Cloud credentials. Token is Fernet-encrypted."""

    label = models.CharField(max_length=255, default="Jira Cloud")
    jira_url = models.URLField(help_text="z.B. https://firma.atlassian.net")
    jira_email = models.EmailField(help_text="Jira-Account-Email fuer API-Zugriff.")
    jira_api_token_encrypted = models.TextField(help_text="Fernet-encrypted API token.")
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Mandantenspezifische Jira-Konfiguration (Schema-IDs, Custom-Field-IDs etc.)",
    )
    is_active = models.BooleanField(default=True)
    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_test_success = models.BooleanField(null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant"],
                condition=models.Q(is_active=True),
                name="unique_active_jira_connection_per_tenant",
            ),
        ]

    def __str__(self):
        return f"[{self.tenant.name}] {self.label}"

    def set_token(self, plaintext: str) -> None:
        """Encrypt and store an API token."""
        self.jira_api_token_encrypted = encrypt_token(plaintext)

    def get_token(self) -> str:
        """Decrypt and return the API token."""
        return decrypt_token(self.jira_api_token_encrypted)


# ---------------------------------------------------------------------------
# TwilioConnection — one active connection per tenant
# ---------------------------------------------------------------------------
class TwilioConnection(TenantScopedModel):
    """Per-tenant Twilio credentials for browser-based telephony. Auth token is Fernet-encrypted."""

    label = models.CharField(max_length=255, default="Twilio Telefonie")
    account_sid = models.CharField(
        max_length=100,
        validators=[RegexValidator(r"^AC[a-f0-9]{32}$", "Account SID muss mit 'AC' beginnen.")],
        help_text="Twilio Account SID (beginnt mit AC).",
    )
    auth_token_encrypted = models.TextField(help_text="Fernet-encrypted Auth Token.")
    twiml_app_sid = models.CharField(
        max_length=100,
        validators=[RegexValidator(r"^AP[a-f0-9]{32}$", "TwiML App SID muss mit 'AP' beginnen.")],
        help_text="TwiML App SID (beginnt mit AP).",
    )
    phone_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r"^\+[1-9]\d{1,14}$", "Telefonnummer muss im E.164-Format sein (z.B. +4930123456).")],
        help_text="Twilio-Telefonnummer im E.164-Format.",
    )
    is_active = models.BooleanField(default=True)
    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_test_success = models.BooleanField(null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant"],
                condition=models.Q(is_active=True),
                name="unique_active_twilio_connection_per_tenant",
            ),
        ]

    def __str__(self):
        return f"[{self.tenant.name}] {self.label}"

    def set_auth_token(self, plaintext: str) -> None:
        """Encrypt and store the auth token."""
        self.auth_token_encrypted = encrypt_token(plaintext)

    def get_auth_token(self) -> str:
        """Decrypt and return the auth token."""
        return decrypt_token(self.auth_token_encrypted)


# ---------------------------------------------------------------------------
# WhatsAppConnection — one active connection per tenant
# ---------------------------------------------------------------------------
class WhatsAppConnection(TenantScopedModel):
    """Per-tenant WhatsApp Business API credentials. Access token is Fernet-encrypted."""

    label = models.CharField(max_length=255, default="WhatsApp Business")
    phone_number_id = models.CharField(
        max_length=100,
        help_text="Meta Phone Number ID (aus dem WhatsApp Business Dashboard).",
    )
    business_account_id = models.CharField(
        max_length=100,
        help_text="WhatsApp Business Account ID (WABA ID).",
    )
    access_token_encrypted = models.TextField(help_text="Fernet-encrypted Meta Access Token.")
    webhook_verify_token = models.CharField(
        max_length=255,
        help_text="Verify-Token fuer Meta Webhook-Verifikation.",
    )
    display_phone_number = models.CharField(
        max_length=20,
        help_text="Anzeige-Nummer im E.164-Format, z.B. +4915112345678.",
    )
    is_active = models.BooleanField(default=True)
    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_test_success = models.BooleanField(null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant"],
                condition=models.Q(is_active=True),
                name="unique_active_whatsapp_connection_per_tenant",
            ),
        ]

    def __str__(self):
        return f"[{self.tenant.name}] {self.label}"

    def set_access_token(self, plaintext: str) -> None:
        """Encrypt and store the access token."""
        self.access_token_encrypted = encrypt_token(plaintext)

    def get_access_token(self) -> str:
        """Decrypt and return the access token."""
        return decrypt_token(self.access_token_encrypted)


# ---------------------------------------------------------------------------
# ActionTemplate — reusable Jira API call template
# ---------------------------------------------------------------------------
class HttpMethod(models.TextChoices):
    GET = "GET", "GET"
    POST = "POST", "POST"
    PUT = "PUT", "PUT"
    DELETE = "DELETE", "DELETE"


class TargetType(models.TextChoices):
    JIRA = "jira", "Jira"
    WEBHOOK = "webhook", "Webhook"


class AuthType(models.TextChoices):
    NONE = "none", "Keine"
    BEARER = "bearer", "Bearer Token"
    BASIC = "basic", "Basic Auth"
    API_KEY = "api_key", "API Key"


class ActionTemplate(TimestampedModel):
    """Template for a single API call (Jira or Webhook) with {{PLACEHOLDER}} syntax."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="action_templates",
        null=True,
        blank=True,
        help_text="NULL = system template, set = tenant-specific.",
    )
    slug = models.SlugField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_type = models.CharField(
        max_length=20,
        choices=TargetType.choices,
        default=TargetType.JIRA,
        help_text="Zieltyp: Jira (ueber JiraConnection) oder Webhook (eigene URL).",
    )
    method = models.CharField(max_length=10, choices=HttpMethod.choices, default=HttpMethod.POST)
    endpoint = models.CharField(
        max_length=500,
        blank=True,
        help_text="Jira REST path, z.B. /rest/api/3/project. Supports {{PLACEHOLDER}}.",
    )
    webhook_url = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Volle URL fuer Webhooks, z.B. https://api.example.com/hook. Supports {{PLACEHOLDER}}.",
    )
    auth_type = models.CharField(
        max_length=20,
        choices=AuthType.choices,
        default=AuthType.NONE,
        help_text="Auth-Typ fuer Webhooks. Jira nutzt die JiraConnection.",
    )
    auth_credentials_encrypted = models.TextField(
        blank=True,
        help_text="Fernet-verschluesselte JSON-Credentials je nach auth_type.",
    )
    body_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Request body with {{PLACEHOLDER}} syntax.",
    )
    headers_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extra headers (merged with auth headers).",
    )
    variables = models.JSONField(
        default=list,
        blank=True,
        help_text="List of expected variable names.",
    )
    output_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON path → variable name for extracting response values.",
    )
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False, help_text="System templates cannot be edited by tenants.")

    def set_auth_credentials(self, credentials: dict) -> None:
        """Encrypt and store auth credentials as JSON."""
        import json
        self.auth_credentials_encrypted = encrypt_token(json.dumps(credentials))

    def get_auth_credentials(self) -> dict:
        """Decrypt and return auth credentials."""
        import json
        if not self.auth_credentials_encrypted:
            return {}
        return json.loads(decrypt_token(self.auth_credentials_encrypted))

    class Meta(TimestampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "slug"],
                name="unique_action_template_per_tenant",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(tenant__isnull=True),
                name="unique_system_action_template_slug",
            ),
        ]

    def __str__(self):
        prefix = self.tenant.name if self.tenant else "System"
        return f"[{prefix}] {self.name}"


# ---------------------------------------------------------------------------
# ActionSequence + SequenceStep — ordered chain of templates
# ---------------------------------------------------------------------------
class ActionSequence(TimestampedModel):
    """Ordered chain of ActionTemplates executed in sequence."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="action_sequences",
        null=True,
        blank=True,
        help_text="NULL = system sequence, set = tenant-specific.",
    )
    slug = models.SlugField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta(TimestampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "slug"],
                name="unique_action_sequence_per_tenant",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(tenant__isnull=True),
                name="unique_system_action_sequence_slug",
            ),
        ]

    def __str__(self):
        prefix = self.tenant.name if self.tenant else "System"
        return f"[{prefix}] {self.name}"


class SequenceStep(TimestampedModel):
    """Single step within a sequence, linking to a template with optional delay."""

    sequence = models.ForeignKey(
        ActionSequence,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    template = models.ForeignKey(
        ActionTemplate,
        on_delete=models.CASCADE,
        related_name="sequence_steps",
    )
    position = models.PositiveIntegerField()
    delay_seconds = models.PositiveIntegerField(default=0, help_text="Delay before executing this step.")
    is_active = models.BooleanField(default=True)

    class Meta(TimestampedModel.Meta):
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["sequence", "position"],
                name="unique_integration_step_position",
            ),
        ]

    def __str__(self):
        return f"Step {self.position}: {self.template.slug} (+{self.delay_seconds}s)"


# ---------------------------------------------------------------------------
# ActionExecution — tracks a running/completed execution
# ---------------------------------------------------------------------------
class ExecutionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class ActionExecution(TenantScopedModel):
    """Tracks execution of a single action or sequence."""

    sequence = models.ForeignKey(
        ActionSequence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="executions",
    )
    template = models.ForeignKey(
        ActionTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="executions",
    )
    status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING,
    )
    input_context = models.JSONField(default=dict, blank=True, help_text="Input variables for the execution.")
    accumulated_context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Accumulated outputs from completed steps (for forwarding between steps).",
    )
    current_step = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="integration_executions",
    )
    entity_type = models.CharField(max_length=100, blank=True, help_text="Cross-ref type, z.B. 'client'.")
    entity_id = models.CharField(max_length=255, blank=True, help_text="Cross-ref ID, z.B. client UUID.")
    celery_task_id = models.CharField(max_length=255, blank=True)
    idempotency_key = models.CharField(max_length=255, blank=True, db_index=True)

    class Meta(TenantScopedModel.Meta):
        pass

    def __str__(self):
        target = self.sequence.slug if self.sequence else (self.template.slug if self.template else "?")
        return f"[{self.status}] {target}"


# ---------------------------------------------------------------------------
# StepLog — immutable log per executed step
# ---------------------------------------------------------------------------
class StepLogStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"


class StepLog(TenantScopedModel):
    """Immutable log of a single step execution with full request/response data."""

    execution = models.ForeignKey(
        ActionExecution,
        on_delete=models.CASCADE,
        related_name="step_logs",
    )
    template = models.ForeignKey(
        ActionTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="step_logs",
    )
    position = models.PositiveIntegerField(default=0)
    method = models.CharField(max_length=10, blank=True)
    url = models.URLField(max_length=1000, blank=True)
    request_body = models.JSONField(default=dict, blank=True)
    request_headers = models.JSONField(default=dict, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    response_body = models.JSONField(default=dict, blank=True)
    response_headers = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StepLogStatus.choices,
        default=StepLogStatus.SUCCESS,
    )
    error_message = models.TextField(blank=True)
    extracted_outputs = models.JSONField(default=dict, blank=True, help_text="Values extracted via output_mapping.")
    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"[{self.status}] Step {self.position} → {self.status_code or '?'}"


# ---------------------------------------------------------------------------
# TenantIntegration — tracks which integrations a tenant has enabled
# ---------------------------------------------------------------------------
class TenantIntegration(TenantScopedModel):
    """Per-tenant toggle for an integration type (from the registry)."""

    integration_type = models.CharField(max_length=50)
    is_enabled = models.BooleanField(default=True)
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Integrationsspezifische Konfiguration (z.B. confluence_parent_page_id).",
    )
    enabled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enabled_integrations",
    )

    class Meta(TenantScopedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "integration_type"],
                name="unique_tenant_integration_type",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.integration_type not in get_valid_keys():
            raise ValidationError({"integration_type": f"Unbekannter Integrationstyp: {self.integration_type}"})

    def __str__(self):
        status = "aktiv" if self.is_enabled else "inaktiv"
        return f"[{self.tenant.name}] {self.integration_type} ({status})"


# ---------------------------------------------------------------------------
# ClientIntegrationData — per-client data for an integration type
# ---------------------------------------------------------------------------
class ClientIntegrationData(TenantScopedModel):
    """Stores integration-specific field values for a client (e.g. Jira project URL)."""

    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="integration_data",
    )
    integration_type = models.CharField(max_length=50)
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Feld-Werte als {field_key: value}, validiert gegen die Registry.",
    )

    class Meta(TenantScopedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["client", "integration_type"],
                name="unique_client_integration_type",
            ),
        ]

    def __str__(self):
        return f"[{self.client.name}] {self.integration_type}"
