from dj_rest_auth.registration.views import VerifyEmailView
from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.emails.views import SendGridInboundWebhookView
from apps.integrations.views import WhatsAppWebhookView


def health_check(request):
    checks = {}
    healthy = True

    # Database
    try:
        from django.db import connection
        connection.ensure_connection()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = str(e)
        healthy = False

    # Redis
    try:
        import redis as redis_lib
        from django.conf import settings as django_settings
        r = redis_lib.from_url(django_settings.CELERY_BROKER_URL)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = str(e)
        healthy = False

    status_code = 200 if healthy else 503
    return JsonResponse({"status": "ok" if healthy else "unhealthy", "checks": checks}, status=status_code)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    # allauth URL patterns (needed for internal reverse lookups like email confirmation)
    path("accounts/", include("allauth.urls")),
    path("api/v1/auth/registration/account-confirm-email/<str:key>/", VerifyEmailView.as_view(), name="account_confirm_email"),
    path("api/v1/auth/", include("apps.users.urls", namespace="users")),
    path("api/v1/tenants/", include("apps.tenants.urls", namespace="tenants")),
    path("api/v1/members/", include("apps.users.member_urls", namespace="members")),
    path("api/v1/billing/", include("apps.billing.urls", namespace="billing")),
    path("api/v1/audit/", include("apps.audit.urls", namespace="audit")),
    path("api/v1/emails/", include("apps.emails.urls", namespace="emails")),
    # Inbound Parse webhook (public, no tenant header — separate from email app URLs)
    path("api/v1/emails/inbound-webhook/<uuid:tenant_id>/",
         SendGridInboundWebhookView.as_view(), name="inbound-webhook"),
    path("api/v1/clients/", include("apps.clients.urls", namespace="clients")),
    path("api/v1/service-types/", include("apps.clients.service_type_urls", namespace="service-types")),
    path("api/v1/integrations/", include("apps.integrations.urls", namespace="integrations")),
    path("api/v1/tasks/", include("apps.tasks.urls", namespace="tasks")),
    path("api/v1/nps/", include("apps.nps.urls", namespace="nps")),
    # WhatsApp webhook (public, no tenant header)
    path("api/v1/integrations/whatsapp/webhook/", WhatsAppWebhookView.as_view(), name="whatsapp-webhook"),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
