from fastapi import APIRouter

from app.api.routes import (
    anonymous_sessions,
    career_direction,
    career_journey,
    career_translation,
    catalogue,
    health,
    profile,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(anonymous_sessions.router)
api_router.include_router(catalogue.router)
api_router.include_router(profile.router)
api_router.include_router(career_journey.router)
api_router.include_router(career_translation.router)
api_router.include_router(career_direction.router)
