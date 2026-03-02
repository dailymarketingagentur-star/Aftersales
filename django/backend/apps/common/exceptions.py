import structlog
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

logger = structlog.get_logger()


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data["status_code"] = response.status_code
    else:
        logger.error("unhandled_exception", exc=str(exc), view=str(context.get("view")))

    return response


class SubscriptionRequired(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "An active subscription is required."
    default_code = "subscription_required"
