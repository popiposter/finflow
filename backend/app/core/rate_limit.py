"""Very small in-memory rate limiter for sensitive endpoints."""

from __future__ import annotations

from collections import defaultdict, deque
from time import monotonic
from typing import Deque

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Fixed-window-like limiter backed by per-key timestamp deques."""

    def __init__(self) -> None:
        self._events: dict[str, Deque[float]] = defaultdict(deque)

    def reset(self) -> None:
        """Clear tracked counters, primarily for tests."""
        self._events.clear()

    def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        """Raise if the key exceeds the configured rate limit."""
        now = monotonic()
        window_start = now - window_seconds
        events = self._events[key]

        while events and events[0] <= window_start:
            events.popleft()

        if len(events) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "rate_limited",
                    "message": "Too many requests. Please try again later.",
                },
            )

        events.append(now)


rate_limiter = InMemoryRateLimiter()


def _request_identity(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def build_rate_limit_key(request: Request, scope: str) -> str:
    """Create a stable key for a request scope and caller identity."""
    return f"{scope}:{_request_identity(request)}"
