"""Schemas package."""

from app.schemas.auth import (
    ApiTokenCreate,
    ApiTokenOut,
    ApiTokenOutWithToken,
    LoginRequest,
    Token,
    TokenRefresh,
    UserCreate,
    UserOut,
)
from app.schemas.finance import (
    AccountCreate,
    AccountOut,
    CategoryCreate,
    CategoryOut,
    TransactionCreate,
    TransactionOut,
)
from app.schemas.parse_create import (
    ParseAndCreateResponse,
    ParsedResult,
    ParseErrorResponse,
    ParseRequest,
    TransactionCreateRequest,
)

__all__ = [
    # Auth
    "UserCreate",
    "UserOut",
    "LoginRequest",
    "Token",
    "TokenRefresh",
    "ApiTokenCreate",
    "ApiTokenOut",
    "ApiTokenOutWithToken",
    # Finance
    "AccountCreate",
    "AccountOut",
    "CategoryCreate",
    "CategoryOut",
    "TransactionCreate",
    "TransactionOut",
    # Parse-and-create
    "ParseRequest",
    "ParsedResult",
    "TransactionCreateRequest",
    "ParseAndCreateResponse",
    "ParseErrorResponse",
]
