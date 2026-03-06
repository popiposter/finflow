# Testing snippets

## Test layers
- unit: service logic without real database
- integration: repository/database behavior
- api: HTTP tests against FastAPI app

## First required test
Health endpoint returns 200 and expected payload.

## Running tests

### Unit tests (no Docker required)
```bash
pytest tests/unit/ -v
```

### Integration/API tests (require PostgreSQL)
```bash
# With Testcontainers (local development, requires Docker)
pytest tests/integration/ -v

# With API tests included
pytest tests/api/ -v

# All tests
pytest tests/ -v
```

### Run DB-dependent tests with custom DATABASE_URL
```bash
# For CI or local dev database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db pytest tests/ -v
```

## Test markers
- `@pytest.mark.unit` - Unit tests, no database required
- `@pytest.mark.integration` - Integration tests, require PostgreSQL
- `@pytest.mark.api` - API tests, require FastAPI + PostgreSQL

## CI workflow
- `backend-quick-checks` job: Runs linting, type-checking (no Docker or PostgreSQL)
- `backend-db-tests` job: Runs integration tests with PostgreSQL service container

## Test fixtures (see `backend/tests/postgres.py`)
- `database_url` - Get connection URL (uses TESTcontainers or DATABASE_URL)
- `db_engine` - Async SQLAlchemy engine
- `db_session` - Isolated async database session with automatic rollback
- `clean_db` - Schema setup/teardown for tests

## Test coverage
- `tests/integration/test_database.py` - Real DB-backed tests validating the test infrastructure
