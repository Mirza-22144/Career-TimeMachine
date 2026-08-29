from fastapi import APIRouter
from app.api.routes import health, anonymous_sessions  # add anonymous_sessions

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(anonymous_sessions.router)   # NEW