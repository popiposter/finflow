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
# With Testcontainers (local development)
pytest tests/integration/ -v

# With API tests included
pytest tests/api/ -v
```

### All tests
```bash
pytest tests/ -v
```

### Exclude DB-dependent tests
```bash
pytest tests/ -m "not integration"
```

## Test markers
- `@pytest.mark.unit` - Unit tests, no database required
- `@pytest.mark.integration` - Integration tests, require PostgreSQL
- `@pytest.mark.api` - API tests, require FastAPI + PostgreSQL

## CI workflow
- `backend-quick-checks` job: Runs unit tests, linting, type-checking (no Docker)
- `backend-db-tests` job: Runs integration tests with PostgreSQL service container

## Test fixtures (see `backend/tests/postgres.py`)
- `postgres_container` - Start/stop PostgreSQL container via Testcontainers
- `db_url` - Get connection URL for test database
- `db_engine` - Async SQLAlchemy engine
- `db_session` - Isolated async database session
- `clean_db` - Schema setup/teardown for tests
