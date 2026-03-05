import uuid

from django.db import models

from apps.common.encryption import decrypt_token, encrypt_token
from apps.common.models import TenantScopedModel, TimestampedModel


# ------------------------------------------------------------------
# Email Provider Connection (per-tenant SMTP / SendGrid)
# ------------------------------------------------------------------


class EmailProviderType(models.TextChoices):
    SMTP = "smtp", "SMTP"
    SENDGRID = "sendgrid", "SendGrid"


class EmailProviderConnection(TenantScopedModel):
    """Per-tenant email provider configuration. Supports SMTP and SendGrid."""

    provider_type = models.CharField(max_length=20, choices=EmailProviderType.choices)
    label = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)

    # SMTP fields
    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_password_encrypted = models.TextField(blank=True, help_text="Fernet-encrypted SMTP password.")
    smtp_use_tls = models.BooleanField(default=True)

    # SendGrid fields
    sendgrid_api_key_encrypted = models.TextField(blank=True, help_text="Fernet-encrypted SendGrid API key.")

    # Shared sender info
    from_email = models.EmailField(help_text="Absender-Email-Adresse.")
    from_name = models.CharField(max_length=255, blank=True, help_text="Absender-Anzeigename.")

    # Inbound Parse (SendGrid only)
    inbound_parse_enabled = models.BooleanField(default=False)
    inbound_parse_domain = models.CharField(max_length=255, blank=True)

    # Test status
    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_test_success = models.BooleanField(null=True, blank=True)
    last_test_message = models.TextField(blank=True)

    class Meta(TenantScopedModel.Meta):
        constraints = [
            # Max one SMTP + one SendGrid per tenant
            models.UniqueConstraint(
                fields=["tenant", "provider_type"],
                name="unique_email_provider_per_tenant",
            ),
            # Only one active provider per tenant
            models.UniqueConstraint(
                fields=["tenant"],
                condition=models.Q(is_active=True),
                name="unique_active_email_provider_per_tenant",
            ),
        ]

    def __str__(self):
        status = "aktiv" if self.is_active else "inaktiv"
        return f"[{self.tenant.name}] {self.label} ({status})"

    # -- Encrypted field helpers (same pattern as JiraConnection) --

    def set_smtp_password(self, plaintext: str) -> None:
        self.smtp_password_encrypted = encrypt_token(plaintext)

    def get_smtp_password(self) -> str:
        if not self.smtp_password_encrypted:
            return ""
        return decrypt_token(self.smtp_password_encrypted)

    def set_sendgrid_api_key(self, plaintext: str) -> None:
        self.sendgrid_api_key_encrypted = encrypt_token(plaintext)

    def get_sendgrid_api_key(self) -> str:
        if not self.sendgrid_api_key_encrypted:
            return ""
        return decrypt_token(self.sendgrid_api_key_encrypted)


# ------------------------------------------------------------------
# Email Templates
# ------------------------------------------------------------------


class EmailTemplate(TimestampedModel):
    """Reusable email template with {{PLACEHOLDER}} syntax."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="email_templates",
        null=True,
        blank=True,
        help_text="NULL = system default, set = tenant override.",
    )
    slug = models.SlugField(max_length=100)
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=500, help_text="Supports {{PLACEHOLDER}} syntax.")
    body_html = models.TextField(help_text="HTML body with {{PLACEHOLDER}} syntax.")
    body_text = models.TextField(blank=True, help_text="Plain-text fallback.")
    variables = models.JSONField(
        default=list,
        blank=True,
        help_text="List of expected variable names (documentation only).",
    )
    is_active = models.BooleanField(default=True)

    class Meta(TimestampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "slug"],
                name="unique_email_template_per_tenant",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(tenant__isnull=True),
                name="unique_system_email_template_slug",
            ),
        ]

    def __str__(self):
        prefix = self.tenant.name if self.tenant else "System"
        return f"[{prefix}] {self.name}"


class EmailStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class EmailLog(TimestampedModel):
    """Immutable log of every email sent or scheduled."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="email_logs",
    )
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )
    template_slug = models.CharField(max_length=100, help_text="Denormalized for audit.")
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=500, help_text="Rendered subject.")
    body_html = models.TextField(help_text="Rendered HTML body.")
    status = models.CharField(
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING,
    )
    error_message = models.TextField(blank=True)
    context = models.JSONField(default=dict, blank=True, help_text="Variables used for rendering.")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=255, unique=True)
    sequence_enrollment = models.ForeignKey(
        "SequenceEnrollment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_logs",
    )
    celery_task_id = models.CharField(max_length=255, blank=True)
    tracking_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)

    class Meta(TimestampedModel.Meta):
        pass

    def __str__(self):
        return f"[{self.status}] {self.template_slug} → {self.recipient_email}"


class EmailSequence(TimestampedModel):
    """Ordered collection of email templates sent over time."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="email_sequences",
        null=True,
        blank=True,
        help_text="NULL = system default, set = tenant override.",
    )
    slug = models.SlugField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta(TimestampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "slug"],
                name="unique_email_sequence_per_tenant",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(tenant__isnull=True),
                name="unique_system_email_sequence_slug",
            ),
        ]

    def __str__(self):
        prefix = self.tenant.name if self.tenant else "System"
        return f"[{prefix}] {self.name}"


class SequenceStep(TimestampedModel):
    """Single step within a sequence, linking to a template with a delay."""

    sequence = models.ForeignKey(
        EmailSequence,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        related_name="sequence_steps",
    )
    position = models.PositiveIntegerField()
    delay_days = models.PositiveIntegerField(default=0)
    delay_hours = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta(TimestampedModel.Meta):
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["sequence", "position"],
                name="unique_step_position_per_sequence",
            ),
        ]

    @property
    def total_delay_seconds(self):
        return (self.delay_days * 86400) + (self.delay_hours * 3600)

    def __str__(self):
        return f"Step {self.position}: {self.template.slug} (+{self.delay_days}d {self.delay_hours}h)"


class EnrollmentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class SequenceEnrollment(TimestampedModel):
    """Tracks a recipient's progress through a sequence."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="sequence_enrollments",
    )
    sequence = models.ForeignKey(
        EmailSequence,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    recipient_email = models.EmailField()
    context = models.JSONField(default=dict, blank=True, help_text="Shared variables for all steps.")
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    current_step = models.PositiveIntegerField(default=0)

    class Meta(TimestampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "sequence", "recipient_email"],
                name="unique_enrollment_per_recipient",
            ),
        ]

    def __str__(self):
        return f"[{self.status}] {self.recipient_email} → {self.sequence.slug}"


# ------------------------------------------------------------------
# Inbound Email (received via SendGrid Inbound Parse)
# ------------------------------------------------------------------


class InboundEmail(TenantScopedModel):
    """Incoming email received via SendGrid Inbound Parse webhook."""

    from_email = models.EmailField()
    from_name = models.CharField(max_length=255, blank=True)
    to_email = models.EmailField()
    subject = models.CharField(max_length=500, blank=True)
    body_text = models.TextField(blank=True)
    client = models.ForeignKey(
        "clients.Client",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inbound_emails",
    )
    has_attachments = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    is_assigned = models.BooleanField(default=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["-created_at"]

    def __str__(self):
        status = "gelesen" if self.is_read else "ungelesen"
        return f"[{status}] {self.from_email}: {self.subject[:50]}"


# ------------------------------------------------------------------
# WhatsApp Messages (via Meta Cloud API)
# ------------------------------------------------------------------


class WhatsAppMessageDirection(models.TextChoices):
    INBOUND = "inbound", "Eingehend"
    OUTBOUND = "outbound", "Ausgehend"


class WhatsAppMessageType(models.TextChoices):
    TEXT = "text", "Text"
    IMAGE = "image", "Bild"
    DOCUMENT = "document", "Dokument"
    AUDIO = "audio", "Audio"
    VIDEO = "video", "Video"
    TEMPLATE = "template", "Template"


class WhatsAppMessageStatus(models.TextChoices):
    RECEIVED = "received", "Empfangen"
    SENT = "sent", "Gesendet"
    DELIVERED = "delivered", "Zugestellt"
    READ = "read", "Gelesen"
    FAILED = "failed", "Fehlgeschlagen"


class WhatsAppMessage(TenantScopedModel):
    """WhatsApp message sent or received via Meta Cloud API."""

    wa_message_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Meta Message ID (wamid.xxx).",
    )
    direction = models.CharField(
        max_length=10,
        choices=WhatsAppMessageDirection.choices,
    )
    from_number = models.CharField(max_length=20)
    to_number = models.CharField(max_length=20)
    body_text = models.TextField(blank=True)
    message_type = models.CharField(
        max_length=20,
        choices=WhatsAppMessageType.choices,
        default=WhatsAppMessageType.TEXT,
    )
    status = models.CharField(
        max_length=20,
        choices=WhatsAppMessageStatus.choices,
        default=WhatsAppMessageStatus.RECEIVED,
    )
    client = models.ForeignKey(
        "clients.Client",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="whatsapp_messages",
    )
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw-Webhook-Payload oder zusaetzliche Daten.",
    )

    class Meta(TenantScopedModel.Meta):
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.direction}] {self.from_number} → {self.to_number}: {self.body_text[:50]}"
