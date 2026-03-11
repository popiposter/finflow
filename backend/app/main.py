"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.v1.router import router
from app.core.config import settings
from app.scheduler import ProjectionSchedulerManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    # Startup tasks
    await app.state.scheduler_manager.start()
    yield
    # Shutdown tasks
    await app.state.scheduler_manager.shutdown()


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.state.scheduler_manager = ProjectionSchedulerManager()
    app.include_router(router)

    return app


app = create_app()


def main() -> None:
    """Run uvicorn server."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
