# CLAUDE.md

## Project purpose
FinFlow is a personal finance system focused on:
- actual expenses and income
- planned and recurring payments
- credit card lifecycle tracking
- BDR/P&L style reporting by accrual date
- BDDS/cashflow reporting by cash movement date
- iOS Shortcut ingestion of free-form text that backend parses into structured transactions

## Fixed stack
- Python 3.12+
- FastAPI
- SQLAlchemy 2.x async
- Alembic
- PostgreSQL
- Pydantic v2
- pwdlib for password hashing
- PyJWT for JWT creation/validation
- pytest + pytest-asyncio/anyio + httpx for tests

## Architecture rules
- Keep clear layers: api -> services -> repositories -> db/models.
- API routes must not contain business logic.
- Services orchestrate use-cases.
- Repositories encapsulate database access.
- Pydantic schemas stay separate from SQLAlchemy models.
- Use async database access everywhere.
- Prefer explicit types and small functions.

## Security rules
- Never store plain-text passwords.
- Store only password hashes.
- Access and refresh tokens for web auth must be issued by backend and delivered via HttpOnly Secure cookies.
- Long-lived API tokens for iOS Shortcut must be shown once and stored only as hashes in the database.
- Do not log secrets, tokens, passwords, or raw authorization headers.

## Working rules for Claude Code
- Before implementing a feature, read this file and IMPLEMENTATION.md.
- Update IMPLEMENTATION.md before and after significant work.
- For medium/large tasks, first produce a short implementation plan, then execute it.
- Do not introduce alternative frameworks or libraries without explicit approval.
- Do not rewrite unrelated files.
- Preserve architecture consistency.

## Backend layout
```text
backend/
  app/
    api/
      v1/
    core/
    db/
    models/
    repositories/
    schemas/
    services/
    tasks/
  tests/
    api/
    integration/
    unit/
```

## Testing policy
- New business logic requires unit tests.
- New endpoints require API tests.
- Repository behavior that depends on SQL should have integration tests.
- Write or update tests in the same change as production code.
- Prefer happy-path tests first, then add authorization, validation, and edge cases.

## Delivery policy
For each implemented feature, provide:
1. summary of changed files
2. key design decisions
3. commands to run formatters/tests
4. remaining risks or TODOs
