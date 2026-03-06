# Backend stack decisions

## Chosen stack
- Python 3.12+
- FastAPI
- SQLAlchemy 2.x async
- Alembic
- PostgreSQL
- Pydantic v2
- pwdlib
- PyJWT
- httpx
- pytest + anyio

## Why these are fixed
- Popular and well-documented in current Python backend practice.
- Good fit for async API + relational domain modeling.
- Strong amount of example code exists, so AI coding assistance is more reliable.

## Implementation rules
- Use application factory or a clearly isolated app bootstrap.
- Centralize config under `app/core/config.py`.
- Centralize security helpers under `app/core/security.py`.
- Centralize DB engine/session setup under `app/db/`.
- API routers live under `app/api/v1/`.
- Avoid putting SQL in routes.
