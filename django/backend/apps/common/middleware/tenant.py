from django.http import JsonResponse

TENANT_HEADER = "HTTP_X_TENANT_ID"
EXEMPT_PATHS = [
    "/admin/",
    "/health/",
    "/stripe/",
    "/api/v1/auth/login/",
    "/api/v1/auth/registration/",
    "/api/v1/auth/token/refresh/",
    "/api/v1/auth/password/reset/",
    "/api/v1/auth/me/",
    "/api/v1/auth/tenants/",
    "/api/v1/tenants/",
    "/__debug__/",
    "/api/v1/emails/track/",
    "/api/v1/integrations/twilio/twiml/",
    "/api/v1/nps/public/",
]


class TenantMiddleware:
    """
    Sets request.tenant from X-Tenant-ID header.
    Only resolves the tenant — membership validation is handled by
    DRF permissions (IsTenantMember etc.) which run after JWT auth.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None

        if any(request.path.startswith(path) for path in EXEMPT_PATHS):
            return self.get_response(request)

        tenant_id = request.META.get(TENANT_HEADER)
        if not tenant_id:
            return JsonResponse(
                {"detail": "X-Tenant-ID header is required."},
                status=400,
            )

        from apps.tenants.models import Tenant

        try:
            tenant = Tenant.objects.get(id=tenant_id, is_active=True)
        except (Tenant.DoesNotExist, ValueError):
            return JsonResponse(
                {"detail": "Invalid or inactive tenant."},
                status=404,
            )

        request.tenant = tenant
        return self.get_response(request)
