"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import router
from app.core.config import settings
from app.core.error_handlers import (
    build_error_response,
    domain_exception_handler,
    http_exception_handler,
    normalize_unhandled_error,
    request_validation_exception_handler,
)
from app.exceptions import AppDomainError
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
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(AppDomainError, domain_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    return app


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a safe JSON payload for unexpected server errors."""
    status_code, code, message = normalize_unhandled_error(exc)
    logger.exception(
        "Unhandled server error during %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return build_error_response(
        status_code=status_code,
        code=code,
        message=message,
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
