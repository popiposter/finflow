"""Health check endpoint."""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Return health status."""
    return {
        "status": "healthy",
        "app": settings.app_title,
        "version": settings.app_version,
    }
