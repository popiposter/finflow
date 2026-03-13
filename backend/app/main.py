"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import router
from app.core.config import settings
from app.scheduler import ProjectionSchedulerManager

logger = logging.getLogger(__name__)


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
    app.add_exception_handler(Exception, unhandled_exception_handler)

    return app


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a safe JSON payload for unexpected server errors."""
    logger.exception(
        "Unhandled server error during %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


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
