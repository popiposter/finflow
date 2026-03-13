"""Domain exceptions for FinFlow application."""


class AppDomainError(Exception):
    """Base class for structured domain errors."""

    code = "domain_error"
    status_code = 400

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        fields: dict[str, str] | None = None,
    ):
        self.message = message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.fields = fields or {}
        super().__init__(message)


class ConflictError(AppDomainError):
    """Raised when a request conflicts with the current domain state."""

    code = "conflict"
    status_code = 409


class TransactionNotFoundError(AppDomainError):
    """Raised when a transaction is not found."""

    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        super().__init__("Transaction not found", code="transaction_not_found", status_code=404)


class AccountNotFoundError(AppDomainError):
    """Raised when an account is not found or not owned by the user."""

    def __init__(self, account_id: str):
        self.account_id = account_id
        super().__init__("Account not found", code="account_not_found", status_code=404)


class CategoryNotFoundError(AppDomainError):
    """Raised when a category is not found or not owned by the user."""

    def __init__(self, category_id: str):
        self.category_id = category_id
        super().__init__("Category not found", code="category_not_found", status_code=404)


class ProjectionNotFoundError(AppDomainError):
    """Raised when a projected transaction is not found."""

    def __init__(self, projected_transaction_id: str):
        self.projected_transaction_id = projected_transaction_id
        super().__init__(
            "Projected transaction not found",
            code="projected_transaction_not_found",
            status_code=404,
        )


class InvalidProjectionStatusError(ConflictError):
    """Raised when attempting an operation on a projection with invalid status."""

    def __init__(self, projected_transaction_id: str, status: str, allowed_statuses: list[str]):
        self.projected_transaction_id = projected_transaction_id
        self.status = status
        self.allowed_statuses = allowed_statuses
        super().__init__(
            f"Projected transaction has status '{status}'. "
            f"Allowed statuses: {', '.join(allowed_statuses)}",
            code="invalid_projection_status",
        )


class ProjectionVersionMismatchError(ConflictError):
    """Raised when optimistic lock version mismatch occurs."""

    def __init__(self, projected_transaction_id: str, expected_version: int, actual_version: int):
        self.projected_transaction_id = projected_transaction_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Projected transaction version mismatch: "
            f"expected {expected_version}, got {actual_version}",
            code="projection_version_mismatch",
        )


__all__ = [
    "AppDomainError",
    "ConflictError",
    "TransactionNotFoundError",
    "AccountNotFoundError",
    "CategoryNotFoundError",
    "ProjectionNotFoundError",
    "InvalidProjectionStatusError",
    "ProjectionVersionMismatchError",
]
