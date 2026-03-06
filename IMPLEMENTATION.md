# IMPLEMENTATION.md

## Current phase
Project bootstrap, code quality tooling, PostgreSQL-backed test infrastructure, and authentication foundation.

## Goals in progress
- [ ] Create backend project skeleton.
- [ ] Add pyproject.toml with approved dependencies.
- [ ] Add FastAPI application factory and health endpoint.
- [ ] Configure settings management.
- [ ] Configure async SQLAlchemy and Alembic.
- [ ] Add reusable local knowledge packs for new features.
- [ ] Implement PostgreSQL-backed test infrastructure (local + CI).

## Fixed decisions
- Backend is Python/FastAPI only.
- Database is PostgreSQL.
- ORM is async SQLAlchemy 2.x.
- Password hashing uses pwdlib.
- JWT uses PyJWT.
- Web auth uses HttpOnly Secure cookies.
- iOS Shortcut uses long-lived bearer API token stored hashed in DB.
- Code quality stack is Ruff + mypy + pre-commit + GitHub Actions.
- DB-dependent tests use real PostgreSQL, not SQLite.
- Local DB-dependent tests should use Testcontainers.
- CI DB-dependent tests should use GitHub Actions PostgreSQL service containers.

## Agent workflow
- Before coding, Claude must read `CLAUDE.md`, `.claude/rules/*.md`, and relevant docs in `docs/agent/`.
- For each issue: create a short plan, implement in small steps, update docs when a new reusable pattern appears.
- Prefer local examples and snippets to web search.
- If using a new library or pattern, create or update a local note under `docs/agent/`.
- Run fast quality checks during implementation whenever tooling is available.

## Next implementation checklist
1. Create `backend/pyproject.toml`.
2. Create `backend/app/main.py` and `backend/app/core/config.py`.
3. Create `backend/app/api/v1/health.py`.
4. Create app startup wiring and router registration.
5. Add test scaffolding with one health-check API test.
6. Only after scaffold is green, move to auth models and migrations.
7. After bootstrap, wire Ruff, mypy, pre-commit, and CI commands into the actual backend config.
8. After bootstrap, add PostgreSQL test infrastructure for DB-dependent tests.

## Done log
- [x] Repository initialized with Claude-oriented guidance files.
- [x] Added GitHub issue templates, PR template, and workflow placeholders.
- [x] Added local agent docs and reusable implementation playbooks.
- [x] Added initial code-quality guidance and root pre-commit config.
- [x] **Issue #1 - Backend bootstrap** (completed):
  - `backend/pyproject.toml` with FastAPI, SQLAlchemy async, Alembic, Pydantic v2, pytest dependencies
  - `backend/app/core/config.py` with pydantic-settings
  - `backend/app/db/base.py` with SQLAlchemy declarative base
  - `backend/app/db/session.py` with async engine and session factory
  - `backend/app/main.py` with FastAPI app factory and lifespan
  - `backend/app/api/v1/health.py` with health endpoint
  - `backend/app/api/v1/router.py` with API v1 router
  - `backend/alembic.ini` and `backend/alembic_migrations/env.py` for migrations
  - Test scaffold with `backend/tests/api/test_health.py` (3 tests, no DB required)
  - Alembic can discover `Base.metadata` for migrations
  - Alembic migrations stored in `alembic_migrations/` (renamed from `alembic/` to avoid conflict with alembic package)
  - Updated `docs/agent/features/project-bootstrap.md` to reflect `alembic_migrations` path
- [x] **Issue #8 - PostgreSQL test infrastructure** (completed):
  - Added `testcontainers` to dev dependencies in `backend/pyproject.toml`
  - Created `backend/tests/postgres.py` with unified pytest fixtures:
    - Uses `DATABASE_URL` if set (CI) or Testcontainers (local)
    - `database_url`, `db_engine`, `db_session`, `clean_db` fixtures
  - Created `backend/tests/integration/conftest.py` with test markers and fixture exports
  - Created `backend/tests/integration/test_database.py` with real DB-backed tests
  - Updated `backend/tests/integration/__init__.py` with documentation
  - Added test markers (`unit`, `integration`, `api`) to pytest config in `pyproject.toml`
  - Updated `.github/workflows/ci.yml` with two jobs:
    - `backend-quick-checks`: linting, type-checking (no Docker/PostgreSQL)
    - `backend-db-tests`: integration tests with PostgreSQL service container
  - Updated `docs/snippets/testing.md` with test commands and coverage info
- [x] **Issue #2 - Auth foundation** (completed):
  - Models: `User`, `ApiToken` with PostgreSQL UUID types and timestamps
  - Migration: `alembic_migrations/versions/20260306194919_add_auth_tables.py`
  - Security helpers: `hash_password`, `verify_password`, JWT create/decode, API token gen/hash
  - Cookie helpers: `set_access_cookie`, `set_refresh_cookie`, `clear_auth_cookies`
  - Repositories: `UserRepository`, `ApiTokenRepository`
  - Auth service: register, login, refresh, logout, get_current_user, API token CRUD
  - Routes: `/register`, `/login`, `/refresh`, `/logout`, `/me`, `/api-tokens` (GET/POST)
  - Tests: unit, integration, and API tests for all endpoints
  - Updated `IMPLEMENTATION.md` with done log entry for this issue
