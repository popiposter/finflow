# GitHub Actions PostgreSQL snippet pack

## CI approach
- Use a PostgreSQL service container in GitHub Actions.
- Export the test database URL to the test process.
- Wait for readiness using container health checks or readiness command.
- Run migrations before DB-dependent tests.

## Validation stages
1. Ruff check
2. Ruff format --check
3. mypy
4. unit tests
5. integration/API tests against PostgreSQL

## Principle
CI is the final gate, but local DB-dependent tests should be possible without manual database setup.
