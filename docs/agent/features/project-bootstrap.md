# Project bootstrap knowledge pack

## Goal
Create the minimum production-grade backend scaffold for FinFlow so all later features land on a stable foundation.

## Scope
- `backend/pyproject.toml`
- FastAPI app bootstrap
- config/settings
- router registration
- async SQLAlchemy engine and session factory
- Alembic wiring
- health endpoint
- test scaffold

## Required files
- `backend/pyproject.toml`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/api/v1/router.py`
- `backend/app/api/v1/health.py`
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/tests/api/test_health.py`

## Design rules
- Python 3.12+.
- Async stack only.
- Keep route handlers thin.
- Centralize app construction in one place.
- Settings come from environment and are validated.
- Database session dependency should be reusable by services and repositories.

## Accepted libraries
- FastAPI
- Uvicorn
- SQLAlchemy 2.x async
- asyncpg
- Alembic
- Pydantic v2 / pydantic-settings
- httpx
- pytest
- anyio

## Do not do
- Do not add business-domain models yet.
- Do not add auth logic yet.
- Do not place SQL in route files.
- Do not use sync SQLAlchemy engine.
- Do not create multiple config modules.

## Output expectations
- `GET /api/v1/health` returns 200 JSON.
- App starts with one command.
- Tests run locally.
- Alembic can discover metadata.

## Test checklist
- Health endpoint returns expected payload.
- Settings load in test mode.
- App import does not create circular imports.

## Suggested implementation order
1. Add dependencies.
2. Add config.
3. Add app factory and router.
4. Add DB base/session.
5. Add health route.
6. Add tests.
7. Add Alembic.
