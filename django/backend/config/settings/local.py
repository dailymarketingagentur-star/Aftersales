from decouple import config

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Email: use SMTP if configured, otherwise fall back to console output
EMAIL_HOST = config("EMAIL_HOST", default="")
if EMAIL_HOST:
    EMAIL_BACKEND = "apps.common.email_backend.InsecureSMTPBackend"
    EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
    EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
    DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Debug toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
INTERNAL_IPS = ["127.0.0.1", "172.0.0.0/8"]
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG}

# CORS
CORS_ALLOW_ALL_ORIGINS = True

# Simpler password validation for dev
AUTH_PASSWORD_VALIDATORS = []
