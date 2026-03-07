# FinFlow

FinFlow is a backend-first finance application under active bootstrap. The current branch adds the authentication foundation, stabilizes the backend CI pipeline, and introduces a staged testing workflow that is easier to use with AI-assisted development.

## Source of truth

Use these documents in this order:

- `README.md` — project overview and document map.
- `CLAUDE.md` — short repository instructions for AI coding agents.
- `docs/README.md` — index of project documentation.
- `docs/testing-architecture.md` — testing rules and CI expectations.
- `IMPLEMENTATION.md` — current delivery status and next steps.
- External playbook: [claude-github-dev-playbook](https://github.com/popiposter/claude-github-dev-playbook).

## Current backend scope

- FastAPI backend skeleton.
- Health endpoint and settings management.
- Async SQLAlchemy and Alembic.
- Authentication foundation: users, refresh sessions, API tokens, auth routes, and tests.
- CI with fast checks plus full backend test execution.

## Working conventions

- Keep feature tasks small and explicit.
- Prefer feature code plus unit or smoke tests first.
- Add integration or API coverage only in a follow-up task after review.
- Keep runtime code free from test-only sync database paths.
