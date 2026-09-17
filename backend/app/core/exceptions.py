import logging
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Kept as a local constant so a future FastAPI rename does not break this file.
REQUEST_VALIDATION_STATUS_CODE = 422
TOO_MANY_REQUESTS_STATUS_CODE = 429
INTERNAL_SERVER_ERROR_STATUS_CODE = 500


def _error_body(code: str, message: str, details: list[Any] | None = None) -> dict[str, Any]:
    """Build the one error envelope shape used by the whole API."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        }
    }


def _normalise_http_detail(
    status_code: int,
    detail: Any,
) -> tuple[str, str, list[Any]]:
    """Convert any HTTPException detail into code/message/details parts."""
    if isinstance(detail, dict):
        # Services may raise an already structured detail. The handler wraps it
        # in the public {"error": ...} envelope.
        code = detail.get("code", f"HTTP_{status_code}")
        message = detail.get("message", "Request failed")
        raw_details = detail.get("details", [])
        if raw_details is None:
            details = []
        elif isinstance(raw_details, list):
            details = raw_details
        else:
            details = [raw_details]
        return str(code), str(message), details

    # Most existing code raises simple string details. Keep those messages and
    # attach a status-based code so every response still has the same shape.
    if detail is None:
        return f"HTTP_{status_code}", "Request failed", []

    return f"HTTP_{status_code}", str(detail), []


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle FastAPI/Starlette HTTPException with the standard envelope."""
    code, message, details = _normalise_http_detail(exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(code, message, details),
        headers=exc.headers,
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic request validation errors with the standard envelope."""
    details = [
        {
            # loc is a tuple like ("body", "planned_return_date"). Join it so
            # frontend code can display a compact field path.
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=REQUEST_VALIDATION_STATUS_CODE,
        content=jsonable_encoder(
            _error_body(
                "REQUEST_VALIDATION_ERROR",
                "Request validation failed",
                details,
            )
        ),
    )


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """Handle a rate-limit rejection with the standard envelope. The limit
    itself is not echoed back. Limits are per minute, so retrying after 60
    seconds always gets a fresh window."""
    return JSONResponse(
        status_code=TOO_MANY_REQUESTS_STATUS_CODE,
        content=_error_body(
            "RATE_LIMITED",
            "Too many requests. Please wait a minute and try again.",
        ),
        headers={"Retry-After": "60"},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort handler for any exception no other handler caught. The
    full exception is logged server-side only; the client gets the standard
    envelope with a generic message, never a traceback or internal detail."""
    logger.error(
        "Unhandled %s on %s %s",
        type(exc).__name__,
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=INTERNAL_SERVER_ERROR_STATUS_CODE,
        content=_error_body(
            "INTERNAL_SERVER_ERROR",
            "Something went wrong. Please try again.",
        ),
    )
