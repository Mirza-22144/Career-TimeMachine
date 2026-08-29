from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

# Keep this local to avoid framework constant renames affecting our code.
REQUEST_VALIDATION_STATUS_CODE = 422


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
