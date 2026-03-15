# Auth foundation knowledge pack

## Goal
Implement secure user authentication for web and API access.

## Scope
- user model
- password hashing helpers
- JWT access/refresh helpers
- cookie helpers
- auth service
- login / refresh / logout endpoints
- long-lived API tokens for iOS Shortcut and Telegram chat linking
- auth tests

## Required modules
- `backend/app/models/user.py`
- `backend/app/models/api_token.py`
- `backend/app/schemas/auth.py`
- `backend/app/core/security.py`
- `backend/app/core/auth_cookies.py`
- `backend/app/repositories/user_repository.py`
- `backend/app/repositories/api_token_repository.py`
- `backend/app/services/auth_service.py`
- `backend/app/api/v1/auth.py`
- tests under `backend/tests/unit`, `backend/tests/integration`, `backend/tests/api`

## Security rules
- Passwords hashed with `pwdlib.PasswordHash.recommended()`.
- Never store or log raw passwords.
- JWT created with PyJWT.
- Claims must include `sub`, `type`, `exp`, `iat`; add `jti` when useful.
- Web tokens go to HttpOnly Secure cookies.
- API token for Shortcut or Telegram linking is generated once, shown once, stored hashed only.
- Support token revocation and `last_used_at`.

## Cookie rules
- Access cookie and refresh cookie have different names.
- Cookie flags come from config.
- Clearing cookies is centralized in helper functions.

## API endpoints
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/api-tokens`
- `GET /api/v1/auth/me`

## Do not do
- Do not store web auth tokens in localStorage.
- Do not place auth logic directly in routes.
- Do not compare password hashes manually.
- Do not store raw API tokens in DB.

## Test checklist
- Password hash/verify.
- Register happy path.
- Login happy path.
- Login invalid password.
- Refresh works with valid refresh token only.
- Protected route rejects missing/invalid auth.
- API token creation returns raw token once.
- DB stores only token hash.

## Suggested implementation order
1. Add models and migration.
2. Add security helpers.
3. Add repositories.
4. Add service layer.
5. Add routes.
6. Add tests.
7. Verify cookies and auth flows.
