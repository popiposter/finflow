# Backend

This folder contains the application code, migrations, and tests for the current FinFlow backend.

## Primary entry points

- `app/` — FastAPI application code.
- `alembic_migrations/` — schema migrations.
- `tests/` — unit, integration, and API tests.
- `pyproject.toml` — Python dependencies and tool configuration.

## Developer flow

- Implement feature code first.
- Add only the coverage required by the current stage.
- Use `docs/testing-architecture.md` before changing fixtures, DB setup, or CI expectations.
- Keep model definitions aligned with migrations.

## Local checks

Default local pass:

```bash
./scripts/dev/check-backend.sh
./scripts/dev/assert-clean-git.sh
```

The check script uses the uv-managed environment to match CI exactly. This ensures mypy and pytest run with the same tool versions and configuration as GitHub Actions.

If you touch Python code and Ruff is available locally, run it manually before commit:

```bash
cd backend
ruff check .
ruff format .
```

Ruff is advisory rather than a repo-enforced gate.

## Containerized local dev

The repo root contains a `compose.yml` that starts PostgreSQL, the backend, and the frontend together for local development.

Typical flow from the repo root:

```bash
docker compose up --build
```

The backend service:
- bind-mounts `backend/` for live reload
- runs `uv sync --extra dev` inside the container into an isolated named virtualenv volume
- applies `alembic upgrade head` before starting Uvicorn

When dependencies change, restart the service or rerun `docker compose up --build`. When only Python source changes, `--reload` picks them up automatically.

## Practical lessons

- Do not commit temporary `.claude/session-*.md` notes.
- For repository `update()` methods that expose refreshed ORM state, prefer returning a fresh re-read when async session state gets tricky.
- For transaction tests, validate both `date_accrual` and `date_cash` in realistic scenarios rather than only same-day cases.
- For category APIs, validate parent ownership and hierarchy behavior explicitly.
