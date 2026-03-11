"""Health check endpoints."""

from typing import cast

from fastapi import APIRouter, Request

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


@router.get("/health/scheduler", tags=["system"])
async def scheduler_health_check(request: Request) -> dict[str, str | None]:
    """Return scheduler status."""
    scheduler_manager = request.app.state.scheduler_manager
    return cast(dict[str, str | None], scheduler_manager.health())
