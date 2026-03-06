# Auth patterns

## Passwords
- Use pwdlib recommended hasher.
- Expose helper functions:
  - `hash_password(password: str) -> str`
  - `verify_password(password: str, password_hash: str) -> bool`

## JWT
- Use PyJWT.
- Separate helpers for access and refresh creation.
- Required claims:
  - `sub`
  - `type`
  - `exp`
  - `iat`
  - optional `jti`

## Cookies
- Web auth tokens go into HttpOnly Secure cookies.
- Do not store web auth tokens in localStorage.
- Centralize cookie names and TTLs in config.

## API tokens
- Generate random token.
- Show once to user.
- Store only hash in DB.
- Support revoke and `last_used_at`.

## Required tests
- Password hash/verify.
- Access token creation/validation.
- Refresh token rejection for wrong `type`.
- Login happy path.
- Login invalid password.
- Protected route with/without cookie.
