# Testing architecture

## Goals

The backend test stack should stay predictable, fast to debug, and aligned with CI.
The same categories of tests should work locally and in GitHub Actions without hidden fixture contracts.

## Rules

- Keep one canonical top-level async database setup in `backend/tests/conftest.py` for app-level tests.
- Do not add sync-only database engines or sync PostgreSQL driver requirements into application runtime code just to support tests.
- ORM models used by tests must match production migrations on keys, constraints, and important timestamp columns.
- Prefer configuration-driven token/session lifetimes; avoid hardcoded expiry values in services.
- CI must run the full backend suite with `pytest tests/`, not a partial subset that can miss regressions.
- If a test subset requires extra infrastructure, declare its Python dependencies explicitly in CI.

## Fixture guidance

- Use `async_session_factory` for async DB tests.
- Keep fixture scopes simple and explicit; if a setup fixture is session-scoped, its event loop must also be session-scoped.
- Avoid mixing multiple competing app/bootstrap paths inside tests unless a specific isolation scenario requires it.
- Clean database state between tests in one shared place instead of per-file ad hoc helpers.

## CI guidance

- Keep fast static checks in a separate job (`ruff`, format check, `mypy`).
- Keep DB-backed tests in a dedicated job with all required services and Python dependencies installed.
- When CI expands to the full suite, update the workflow before relying on new tests for merge safety.
