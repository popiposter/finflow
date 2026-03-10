"""Domain exceptions for FinFlow application."""


class ProjectionNotFoundError(Exception):
    """Raised when a projected transaction is not found."""

    def __init__(self, projected_transaction_id: str):
        self.projected_transaction_id = projected_transaction_id
        super().__init__(f"Projected transaction not found: {projected_transaction_id}")


class InvalidProjectionStatusError(Exception):
    """Raised when attempting an operation on a projection with invalid status."""

    def __init__(self, projected_transaction_id: str, status: str, allowed_statuses: list[str]):
        self.projected_transaction_id = projected_transaction_id
        self.status = status
        self.allowed_statuses = allowed_statuses
        super().__init__(
            f"Projected transaction {projected_transaction_id} has status '{status}'. "
            f"Allowed statuses: {', '.join(allowed_statuses)}"
        )


class ProjectionVersionMismatchError(Exception):
    """Raised when optimistic lock version mismatch occurs."""

    def __init__(self, projected_transaction_id: str, expected_version: int, actual_version: int):
        self.projected_transaction_id = projected_transaction_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Projected transaction {projected_transaction_id} version mismatch: "
            f"expected {expected_version}, got {actual_version}"
        )


__all__ = [
    "ProjectionNotFoundError",
    "InvalidProjectionStatusError",
    "ProjectionVersionMismatchError",
]
