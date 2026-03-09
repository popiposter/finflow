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
- Run repo checks before push:

```bash
# Bash
./scripts/dev/check-backend.sh
./scripts/dev/assert-clean-git.sh
```

```powershell
# PowerShell
./scripts/dev/check-backend.ps1
./scripts/dev/assert-clean-git.ps1
```

## Formatting and hooks

- `pre-commit run --all-files` already runs the repo Ruff hooks, including formatting.
- CI uses Ruff format check, so the local pre-commit formatter output should match CI.
- If hooks modify files, stage them, amend or commit them, and rerun checks until `git status --short` is empty.
- Never use `git push --no-verify` for normal feature work.

## CI alignment

Backend CI has two layers:

- Fast checks: Ruff, format check, and MyPy.
- DB-backed checks: full `pytest tests/` with PostgreSQL.

## Code quality

The preferred local sequence is:

1. `pre-commit run --all-files`
2. `mypy .`
3. `pytest tests/`
4. `git status --short` must be empty before push

Use the scripts above so the sequence stays consistent.
