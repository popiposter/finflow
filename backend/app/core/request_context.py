"""Request-scoped helpers such as request IDs and access logging."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response

from app.core.config import settings

logger = logging.getLogger("finflow.request")


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach a request ID, emit structured access logs, and return the response."""
    request_id = request.headers.get(settings.request_id_header) or str(uuid4())
    request.state.request_id = request_id

    started_at = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

    response.headers[settings.request_id_header] = request_id
    logger.info(
        json.dumps(
            {
                "event": "http_request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else None,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )
    return response
