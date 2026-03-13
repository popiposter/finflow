"""Centralized API error normalization for FinFlow."""

from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Mapping

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import (
    AccountNotFoundError,
    AppDomainError,
    CategoryNotFoundError,
    ConflictError,
    InvalidProjectionStatusError,
    ProjectionNotFoundError,
    ProjectionVersionMismatchError,
    TransactionNotFoundError,
)
from app.schemas.error import ErrorResponse


def build_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    fields: dict[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Build a normalized JSON error response."""
    payload = ErrorResponse(
        error={
            "code": code,
            "message": message,
            "fields": fields or {},
        }
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
        headers=headers,
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Normalize FastAPI HTTP exceptions."""
    del request
    if not isinstance(exc, HTTPException):
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_error",
            message="Internal server error",
        )
    code, message, fields = normalize_http_exception(exc)
    return build_error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        fields=fields,
        headers=exc.headers,
    )


async def request_validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return normalized field-level validation errors."""
    del request
    if not isinstance(exc, RequestValidationError):
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_error",
            message="Internal server error",
        )
    return build_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="validation_error",
        message="Validation failed",
        fields=extract_validation_fields(exc.errors()),
    )


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Normalize domain errors with explicit error codes."""
    del request
    if not isinstance(exc, AppDomainError):
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_error",
            message="Internal server error",
        )
    return build_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        fields=exc.fields,
    )


def normalize_http_exception(
    exc: HTTPException,
) -> tuple[str, str, dict[str, str]]:
    """Map ad hoc HTTP exceptions into stable API codes."""
    detail = exc.detail
    if isinstance(detail, dict):
        error = detail.get("error")
        if isinstance(error, dict):
            code = str(error.get("code") or "http_error")
            message = str(error.get("message") or "Request failed")
            raw_fields = error.get("fields")
            fields = raw_fields if isinstance(raw_fields, dict) else {}
            return code, message, {str(key): str(value) for key, value in fields.items()}

        code = str(detail.get("code") or default_http_code(exc.status_code, detail))
        message = str(detail.get("message") or detail.get("detail") or "Request failed")
        raw_fields = detail.get("fields")
        fields = raw_fields if isinstance(raw_fields, dict) else {}
        return code, message, {str(key): str(value) for key, value in fields.items()}

    message = str(detail) if detail else "Request failed"
    code = default_http_code(exc.status_code, message)
    return code, message, {}


def default_http_code(status_code: int, message: object) -> str:
    """Infer a stable error code from HTTP status and message text."""
    normalized = str(message).strip().lower()
    mapping: dict[tuple[int, str], str] = {
        (status.HTTP_400_BAD_REQUEST, "uploaded file is empty"): "import_empty_file",
        (status.HTTP_400_BAD_REQUEST, "only .xlsx files are supported"): "import_invalid_file",
        (
            status.HTTP_400_BAD_REQUEST,
            "account_id is required until default account selection is implemented",
        ): "account_required",
        (status.HTTP_401_UNAUTHORIZED, "not authenticated"): "authentication_required",
        (status.HTTP_404_NOT_FOUND, "account not found"): "account_not_found",
        (status.HTTP_404_NOT_FOUND, "category not found"): "category_not_found",
        (status.HTTP_404_NOT_FOUND, "counterparty account not found"): "account_not_found",
        (status.HTTP_404_NOT_FOUND, "transaction not found"): "transaction_not_found",
        (
            status.HTTP_404_NOT_FOUND,
            "projected transaction not found",
        ): "projected_transaction_not_found",
    }
    if (status_code, normalized) in mapping:
        return mapping[(status_code, normalized)]

    if status_code == status.HTTP_401_UNAUTHORIZED:
        return "authentication_failed"
    if status_code == status.HTTP_403_FORBIDDEN:
        return "permission_denied"
    if status_code == status.HTTP_404_NOT_FOUND:
        return "not_found"
    if status_code == status.HTTP_409_CONFLICT:
        return "conflict"
    if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        return "validation_error"
    if status_code >= 500:
        return "internal_error"
    return "request_failed"


def extract_validation_fields(errors: Iterable[dict[str, object]]) -> dict[str, str]:
    """Convert FastAPI validation errors into a flat field map."""
    field_errors: dict[str, str] = {}
    for error in errors:
        location = error.get("loc")
        key = stringify_location(location)
        if key in field_errors:
            continue
        field_errors[key] = str(error.get("msg") or "Invalid value")
    return field_errors


def stringify_location(location: object) -> str:
    """Flatten validation error path for form-level mapping."""
    if not isinstance(location, (list, tuple)):
        return "form"

    parts = [str(part) for part in location if part not in {"body", "query", "path"}]
    return ".".join(parts) if parts else "form"


def normalize_unhandled_error(error: Exception) -> tuple[int, str, str]:
    """Map unexpected exceptions to safe public responses."""
    if isinstance(error, ConflictError):
        return status.HTTP_409_CONFLICT, error.code, error.message
    if isinstance(error, TransactionNotFoundError):
        return status.HTTP_404_NOT_FOUND, error.code, error.message
    if isinstance(error, AccountNotFoundError):
        return status.HTTP_404_NOT_FOUND, error.code, error.message
    if isinstance(error, CategoryNotFoundError):
        return status.HTTP_404_NOT_FOUND, error.code, error.message
    if isinstance(error, ProjectionNotFoundError):
        return status.HTTP_404_NOT_FOUND, error.code, error.message
    if isinstance(error, InvalidProjectionStatusError):
        return status.HTTP_409_CONFLICT, error.code, error.message
    if isinstance(error, ProjectionVersionMismatchError):
        return status.HTTP_409_CONFLICT, error.code, error.message
    return status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", "Internal server error"
