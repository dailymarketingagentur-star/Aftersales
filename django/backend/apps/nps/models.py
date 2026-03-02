import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.common.models import TenantScopedModel


# ---------------------------------------------------------------------------
# NPSCampaign — Wann/wie Surveys verschickt werden
# ---------------------------------------------------------------------------
class NPSCampaign(TenantScopedModel):
    """Defines when and how NPS surveys are sent."""

    class TriggerType(models.TextChoices):
        DAY_OFFSET = "day_offset", "Tag nach Start"
        QUARTERLY = "quarterly", "Quartalsweise"
        MANUAL = "manual", "Manuell"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100)
    trigger_type = models.CharField(max_length=20, choices=TriggerType.choices, default=TriggerType.DAY_OFFSET)
    day_offset = models.PositiveIntegerField(default=90, help_text="Tage nach Client start_date.")
    repeat_interval_days = models.PositiveIntegerField(default=90, help_text="0 = einmalig, >0 = Wiederholung alle X Tage.")
    is_active = models.BooleanField(default=True)
    email_template = models.ForeignKey(
        "emails.EmailTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nps_campaigns",
        help_text="Template mit {{NPS_URL}} Placeholder.",
    )

    class Meta(TenantScopedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["tenant", "slug"], name="unique_nps_campaign_slug_per_tenant"),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()})"


# ---------------------------------------------------------------------------
# NPSSurvey — Eine konkrete Umfrage-Einladung an einen Client
# ---------------------------------------------------------------------------
class NPSSurvey(TenantScopedModel):
    """A concrete survey invitation sent to a client."""

    class Status(models.TextChoices):
        PENDING = "pending", "Ausstehend"
        RESPONDED = "responded", "Beantwortet"
        EXPIRED = "expired", "Abgelaufen"

    campaign = models.ForeignKey(
        NPSCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="surveys",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="nps_surveys",
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nps_surveys",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    email_log = models.ForeignKey(
        "emails.EmailLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nps_surveys",
    )

    class Meta(TenantScopedModel.Meta):
        pass

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    def __str__(self):
        return f"Survey {self.token} → {self.client.name} ({self.get_status_display()})"


# ---------------------------------------------------------------------------
# NPSResponse — Die eigentliche Antwort (0-10 + Kommentar)
# ---------------------------------------------------------------------------
class NPSResponse(TenantScopedModel):
    """The actual NPS response with score and optional comment."""

    class Segment(models.TextChoices):
        PROMOTER = "promoter", "Promoter"
        PASSIVE = "passive", "Passive"
        DETRACTOR = "detractor", "Detractor"

    survey = models.OneToOneField(
        NPSSurvey,
        on_delete=models.CASCADE,
        related_name="response",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="nps_responses",
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    segment = models.CharField(max_length=20, choices=Segment.choices, editable=False)
    comment = models.TextField(blank=True, default="")
    responded_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    class Meta(TenantScopedModel.Meta):
        pass

    def save(self, *args, **kwargs):
        # Auto-calculate segment from score
        if self.score >= 9:
            self.segment = self.Segment.PROMOTER
        elif self.score >= 7:
            self.segment = self.Segment.PASSIVE
        else:
            self.segment = self.Segment.DETRACTOR
        super().save(*args, **kwargs)

    def __str__(self):
        return f"NPS {self.score} ({self.get_segment_display()}) — {self.client.name}"


# ---------------------------------------------------------------------------
# TestimonialRequest — Testimonial-Pipeline fuer Promoter
# ---------------------------------------------------------------------------
class TestimonialRequest(TenantScopedModel):
    """Tracks testimonial requests and their status through the pipeline."""

    class RequestType(models.TextChoices):
        GOOGLE_REVIEW = "google_review", "Google-Bewertung"
        VIDEO = "video", "Video-Testimonial"
        WRITTEN = "written", "Schriftlich"
        DRAFT_APPROVE = "draft_approve", "Entwurf zur Freigabe"

    class Status(models.TextChoices):
        REQUESTED = "requested", "Angefragt"
        ACCEPTED = "accepted", "Zugesagt"
        RECEIVED = "received", "Erhalten"
        PUBLISHED = "published", "Veroeffentlicht"
        DECLINED = "declined", "Abgelehnt"

    nps_response = models.ForeignKey(
        NPSResponse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="testimonial_requests",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="testimonial_requests",
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="testimonial_requests",
    )
    request_type = models.CharField(max_length=20, choices=RequestType.choices, default=RequestType.WRITTEN)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    content = models.TextField(blank=True, default="", help_text="Testimonial-Text.")
    platform_url = models.URLField(blank=True, default="", help_text="Link zur Bewertung.")
    requested_at = models.DateTimeField(default=timezone.now)
    received_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta(TenantScopedModel.Meta):
        pass

    def __str__(self):
        return f"Testimonial ({self.get_request_type_display()}) — {self.client.name} [{self.get_status_display()}]"
