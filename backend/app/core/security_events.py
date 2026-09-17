import logging
from datetime import datetime, timezone

from starlette.requests import Request

# Every security event goes through this one logger, so events can be found
# by logger name ("app.security") or by the "security_event=" prefix.
security_logger = logging.getLogger("app.security")


def log_security_event(event: str, request: Request, **fields: str) -> None:
    """Log one security event as searchable key=value pairs: event type,
    UTC timestamp, method and path (no query string), plus any extra fields.

    Callers must only pass values that are safe to keep in logs - never a
    raw token, profile content, career-break details or submitted text.
    """
    parts = [
        f"security_event={event}",
        f"at={datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"method={request.method}",
        f"path={request.url.path}",
    ]
    parts += [f"{key}={value}" for key, value in fields.items()]
    security_logger.warning(" ".join(parts))
