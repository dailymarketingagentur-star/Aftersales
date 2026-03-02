from django.urls import path

from apps.emails.views import (
    CancelEnrollmentView,
    EmailLogListView,
    EmailProviderListView,
    EmailProviderStatusView,
    EmailSequenceListView,
    EmailTemplateDetailView,
    EmailTemplateListCreateView,
    EnrollmentListView,
    SendEmailView,
    SendGridProviderActivateView,
    SendGridProviderTestView,
    SendGridProviderView,
    SmtpProviderActivateView,
    SmtpProviderTestView,
    SmtpProviderView,
    StartSequenceView,
    TrackClickView,
    TrackOpenView,
)

app_name = "emails"

urlpatterns = [
    # Templates CRUD
    path("templates/", EmailTemplateListCreateView.as_view(), name="template-list-create"),
    path("templates/<uuid:pk>/", EmailTemplateDetailView.as_view(), name="template-detail"),
    # Logs (read-only)
    path("logs/", EmailLogListView.as_view(), name="log-list"),
    # Send action
    path("send/", SendEmailView.as_view(), name="send"),
    # Sequences
    path("sequences/", EmailSequenceListView.as_view(), name="sequence-list"),
    path("sequences/start/", StartSequenceView.as_view(), name="sequence-start"),
    # Enrollments
    path("enrollments/", EnrollmentListView.as_view(), name="enrollment-list"),
    path("enrollments/<uuid:pk>/cancel/", CancelEnrollmentView.as_view(), name="enrollment-cancel"),
    # Public tracking (no auth)
    path("track/<uuid:tracking_id>/open/", TrackOpenView.as_view(), name="track-open"),
    path("track/<uuid:tracking_id>/click/", TrackClickView.as_view(), name="track-click"),
    # Email providers
    path("providers/status/", EmailProviderStatusView.as_view(), name="provider-status"),
    path("providers/", EmailProviderListView.as_view(), name="provider-list"),
    path("providers/smtp/", SmtpProviderView.as_view(), name="provider-smtp"),
    path("providers/smtp/test/", SmtpProviderTestView.as_view(), name="provider-smtp-test"),
    path("providers/smtp/activate/", SmtpProviderActivateView.as_view(), name="provider-smtp-activate"),
    path("providers/sendgrid/", SendGridProviderView.as_view(), name="provider-sendgrid"),
    path("providers/sendgrid/test/", SendGridProviderTestView.as_view(), name="provider-sendgrid-test"),
    path("providers/sendgrid/activate/", SendGridProviderActivateView.as_view(), name="provider-sendgrid-activate"),
]
