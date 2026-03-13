"""Shared API error response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Normalized API error payload."""

    code: str
    message: str
    fields: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Envelope for all non-success API responses."""

    error: ErrorDetail

