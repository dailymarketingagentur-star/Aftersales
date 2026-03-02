from django.http import JsonResponse

SUBSCRIPTION_EXEMPT_PATHS = [
    "/admin/",
    "/health/",
    "/stripe/",
    "/api/v1/auth/",
    "/api/v1/tenants/",
    "/api/v1/billing/",
    "/__debug__/",
    "/api/v1/emails/track/",
    "/api/v1/integrations/twilio/twiml/",
]


class SubscriptionRequiredMiddleware:
    """Returns 402 if the tenant has no active subscription.
    Staff/superusers bypass this check."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(path) for path in SUBSCRIPTION_EXEMPT_PATHS):
            return self.get_response(request)

        if not hasattr(request, "tenant") or request.tenant is None:
            return self.get_response(request)

        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return self.get_response(request)

        try:
            subscription = request.tenant.subscription
            if subscription.is_active:
                return self.get_response(request)
        except Exception:
            pass

        return JsonResponse(
            {"detail": "An active subscription is required.", "code": "subscription_required"},
            status=402,
        )
