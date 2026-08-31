from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router  # import the API router
from app.core.config import CORS_ORIGINS
from app.core.exceptions import (
    http_exception_handler,
    request_validation_exception_handler,
)

app = FastAPI(title="Career TimeMachine API")

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

app.include_router(api_router, prefix="/api/v1")  # include the API router with a prefix 
