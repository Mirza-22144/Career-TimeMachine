from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router  # import the API router
from app.core.exceptions import (
    http_exception_handler,
    request_validation_exception_handler,
)

app = FastAPI(title="Career TimeMachine API")

# Register central handlers before routes are used. These cover all raised
# HTTPException errors and Pydantic request-validation errors.
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(
    RequestValidationError,
    request_validation_exception_handler,
)

app.include_router(api_router, prefix="/api/v1")  # include the API router with a prefix 
