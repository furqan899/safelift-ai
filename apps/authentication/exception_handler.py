from typing import Any, Dict
import logging
import uuid
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response


logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Response | None:
    response = drf_exception_handler(exc, context)

    correlation_id = str(uuid.uuid4())

    if response is None:
        # Unhandled exception - log and return generic error
        logger.exception("Unhandled exception [%s]: %s", correlation_id, str(exc))
        return Response(
            {
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred.",
                    "correlation_id": correlation_id,
                }
            },
            status=500,
        )

    # Normalize known DRF errors
    data = response.data
    logger.warning("Handled exception [%s]: %s", correlation_id, str(data))

    normalized = {
        "error": {
            "code": getattr(getattr(exc, "default_code", None), "value", None)
            or getattr(exc, "default_code", "error"),
            "message": getattr(exc, "detail", data),
            "correlation_id": correlation_id,
        }
    }

    response.data = normalized
    return response

