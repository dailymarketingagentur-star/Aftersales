from urllib.parse import unquote

from dj_rest_auth.jwt_auth import get_refresh_view
from dj_rest_auth.registration.views import RegisterView, VerifyEmailView, ResendEmailVerificationView
from dj_rest_auth.views import LoginView, LogoutView, PasswordResetView
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from . import views


@method_decorator(ensure_csrf_cookie, name="post")
class CsrfLoginView(LoginView):
    """Login view that ensures the CSRF cookie is set in the response."""
    pass


class FixedVerifyEmailView(VerifyEmailView):
    """Decode URL-encoded confirmation keys (Next.js encodes colons as %3A)."""

    def get_serializer(self, *args, **kwargs):
        if args:
            data = args[0]
        elif "data" in kwargs:
            data = kwargs["data"]
        else:
            return super().get_serializer(*args, **kwargs)

        key = data.get("key", "")
        if "%" in key:
            data = {**data, "key": unquote(key)}
            if args:
                args = (data,) + args[1:]
            else:
                kwargs["data"] = data

        return super().get_serializer(*args, **kwargs)


app_name = "users"

urlpatterns = [
    path("login/", CsrfLoginView.as_view(), name="login"),
    path("registration/", RegisterView.as_view(), name="register"),
    path("registration/verify-email/", FixedVerifyEmailView.as_view(), name="rest_verify_email"),
    path("registration/resend-email/", ResendEmailVerificationView.as_view(), name="rest_resend_email"),
    path("token/refresh/", get_refresh_view().as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password/reset/", PasswordResetView.as_view(), name="password-reset"),
    path("me/", views.MeView.as_view(), name="me"),
    path("tenants/", views.UserTenantsView.as_view(), name="user-tenants"),
]
