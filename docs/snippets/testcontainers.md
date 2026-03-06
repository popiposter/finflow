# Testcontainers snippet pack

## Recommended stack
- `pytest`
- `testcontainers[postgres]` or equivalent Python Testcontainers package
- async SQLAlchemy session/engine for app code
- real Postgres only for integration/API tests

## Fixture strategy
- One fixture starts PostgreSQL container and yields connection URL.
- One fixture applies migrations or creates schema for tests.
- One fixture provides isolated DB sessions.
- Keep teardown automatic.

## Test selection strategy
- Unit tests should not require Docker.
- Mark DB-dependent tests explicitly when useful.
- Run fast unit tests often; run DB-dependent tests before PR/merge and for DB-related work.

## CI strategy
- In GitHub Actions, use a Postgres service container instead of local Testcontainers.
- Apply migrations, then run integration/API tests.
