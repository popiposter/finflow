# Testing with PostgreSQL knowledge pack

## Goal
Provide a stable strategy for DB-dependent tests so FinFlow validates real PostgreSQL behavior locally and in CI.

## Chosen strategy
- Unit tests: no database required.
- Integration/API tests locally: PostgreSQL via Testcontainers.
- CI integration/API tests: PostgreSQL service container in GitHub Actions.

## Why this is the default
- SQLAlchemy + PostgreSQL features should be tested against real Postgres, not SQLite.
- Migrations, constraints, numeric/date behavior, and transaction semantics are safer when tested on the actual target database engine.
- Testcontainers gives reproducible local DB startup without requiring a permanently running local database.

## Test layers
### Unit
- No real DB.
- Mock or fake repositories when appropriate.
- Fast enough to run constantly during implementation.

### Integration
- Real PostgreSQL.
- Repository tests, migration smoke checks, transaction handling, DB constraints.

### API
- FastAPI app against a real PostgreSQL test database.
- Covers dependency wiring and request/response behavior with real persistence.

## Local implementation rules
- Use `testcontainers` / PostgreSQL container for DB-dependent tests.
- Test DB must be ephemeral and isolated from dev/prod databases.
- Prefer session-scoped container startup for speed, with per-test cleanup strategy.
- Keep DB test helpers centralized under `backend/tests/`.

## CI implementation rules
- Use GitHub Actions PostgreSQL service container.
- Wait for DB readiness before running migrations/tests.
- Run migrations against the CI test database before integration/API tests.

## Do not do
- Do not use SQLite as a substitute for PostgreSQL integration tests.
- Do not point tests at a developer's persistent local database.
- Do not require Docker for pure unit tests.

## Minimum future deliverables
- Shared pytest fixtures for DB URL, engine/session, and cleanup.
- Separate test commands or markers for unit vs DB-dependent tests.
- CI workflow updated to run DB-dependent tests against PostgreSQL.
