# Backend

This folder contains the application code, migrations, and tests for the current FinFlow backend.

## Primary entry points

- `app/` — FastAPI application code.
- `alembic_migrations/` — schema migrations.
- `tests/` — unit, integration, and API tests.
- `pyproject.toml` — Python dependencies and tool configuration.

## Developer flow

- Implement feature code first.
- Add unit or smoke tests unless the task explicitly asks for more.
- Use `docs/testing-architecture.md` before changing fixtures, DB setup, or CI expectations.
- Keep model definitions aligned with migrations.
- **Run pre-commit hooks before pushing**: `pre-commit run --all-files` (or install hooks with `pre-commit install`)

## CI alignment

Backend CI has two layers:

- Fast checks: Ruff, format check, and MyPy.
- DB-backed checks: full `pytest tests/` with PostgreSQL.

## Code quality

Before committing:

```bash
# Format code
ruff format .

# Check linting
ruff check .

# Type check
mypy .

# Run tests
pytest tests/
```

Or install pre-commit hooks to run checks automatically:

```bash
pre-commit install
```