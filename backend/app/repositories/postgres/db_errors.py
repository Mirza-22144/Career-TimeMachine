import logging

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

DATABASE_UNAVAILABLE_CODE = "DATABASE_UNAVAILABLE"
DATABASE_UNAVAILABLE_MESSAGE = "We couldn't complete your request. Please try again."


def database_unavailable(exc: Exception) -> HTTPException:
    """Log a database driver failure server-side and build the structured
    503 error core/exceptions.py wraps in the standard envelope (same shape
    as practice_error). The client never sees the driver's message, which
    can include hosts, SQL text or table names."""
    logger.error("Database operation failed (%s)", type(exc).__name__, exc_info=exc)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": DATABASE_UNAVAILABLE_CODE, "message": DATABASE_UNAVAILABLE_MESSAGE},
    )
