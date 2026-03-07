# Testing architecture

## Goals

The backend test stack should stay predictable, fast to debug, and aligned with CI.
The same categories of tests should work locally and in GitHub Actions without hidden fixture contracts.

## Delivery flow

1. Implement feature code and stop at unit or smoke coverage first.
2. Request human review of the feature code before expanding the test harness.
3. Run a separate explicit task for integration and API tests after review, using this document as the contract.
4. Only after that, widen CI coverage or add heavier fixtures if the scope still justifies it.

## Rules

- Keep one canonical top-level async database setup in `backend/tests/conftest.py` for app-level tests.
- Do not add sync-only database engines or sync PostgreSQL driver requirements into application runtime code just to support tests.
- ORM models used by tests must match production migrations on keys, constraints, and important timestamp columns.
- Prefer configuration-driven token and session lifetimes; avoid hardcoded expiry values in services.
- CI must run the full backend suite with `pytest tests/`, not a partial subset that can miss regressions.
- If a test subset requires extra infrastructure, declare its Python dependencies explicitly in CI.
- Do not let an AI agent invent a large bespoke fixture system before the feature itself has been reviewed.

## Fixture guidance

- Use `async_session_factory` for async DB tests.
- Prefer function-scoped DB schema setup unless a broader scope is truly necessary and explicitly supported by pytest-asyncio.
- Keep fixture scopes simple and explicit; avoid hidden coupling between event-loop scope and database bootstrap scope.
- Avoid mixing multiple competing app or bootstrap paths inside tests unless a specific isolation scenario requires it.
- Clean database state in one shared place instead of per-file ad hoc helpers.

## CI guidance

- Keep fast static checks in a separate job (`ruff`, format check, `mypy`).
- Keep DB-backed tests in a dedicated job with all required services and Python dependencies installed.
- When CI expands to the full suite, update the workflow before relying on new tests for merge safety.
- Prefer CI failures that point to missing dependencies or schema mismatches early, before deeper behavioral debugging.
