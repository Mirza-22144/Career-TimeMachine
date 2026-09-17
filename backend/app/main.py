import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router  # import the API router
from app.core.config import CORS_ORIGINS, HAS_DATABASE
from app.core.exceptions import (
    http_exception_handler,
    rate_limit_exceeded_handler,
    request_validation_exception_handler,
    unhandled_exception_handler,
)
from app.api.dependencies import _role_predictor
from app.core.logging_config import configure_logging
from app.core.rate_limit import limiter

configure_logging()
logger = logging.getLogger(__name__)


def log_storage_mode() -> None:
    """Say at startup whether data goes to the database or to memory
    (pen-test R09), so a deployment that silently fell back to in-memory
    storage is easy to spot. Never logs connection settings."""
    if HAS_DATABASE:
        logger.info("Storage mode: database (PostgreSQL)")
    else:
        logger.warning(
            "Storage mode: in-memory (DB_* settings not set) - sessions, profiles "
            "and practice data are lost on restart"
        )


def log_role_prediction_availability() -> None:
    """Say at startup whether the role-prediction model loaded, for the
    same reason as log_storage_mode: a silent fallback (here, every
    GET /practice-role/predicted returning 503) should be easy to spot
    rather than discovered from a support ticket."""
    if _role_predictor is not None:
        logger.info("Role prediction: enabled")
    else:
        logger.warning("Role prediction: unavailable - GET /practice-role/predicted will return 503")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_storage_mode()
    log_role_prediction_availability()
    yield


# debug is pinned off on purpose: with debug=True, Starlette skips the
# catch-all Exception handler below and returns a traceback page instead.
app = FastAPI(title="Career TimeMachine API", debug=False, lifespan=lifespan)
# slowapi looks the limiter up on app.state.
app.state.limiter = limiter

# Allows the frontend (a different origin/port) to call this API from the
# browser. Without this, every request from the React app is blocked by
# the browser's CORS policy before it even reaches here (curl/Postman
# aren't affected, which is why this was easy to miss).
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register central handlers before routes are used. These cover all raised
# HTTPException errors and Pydantic request-validation errors.
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(
    RequestValidationError,
    request_validation_exception_handler,
)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
# Last resort for anything else (e.g. a bug): logged server-side, returned to
# the client as a generic 500 in the same envelope.
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(api_router, prefix="/api/v1")  # include the API router with a prefix 
