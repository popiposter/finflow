# FinFlow

FinFlow is a backend-first finance application under active bootstrap. The repository now uses a compact documentation layout so contributors can find the right source of truth quickly.

## Start here

- `README.md` — project overview and navigation.
- `backend/README.md` — backend developer entry point.
- `CLAUDE.md` — short repository contract for AI agents.
- `docs/README.md` — documentation map.
- `docs/testing-architecture.md` — testing and CI rules.
- `IMPLEMENTATION.md` — current delivery status.
- `PLAYBOOK.md` — local pointer to the external private playbook.

## Current scope

- FastAPI backend skeleton.
- Health endpoint and settings management.
- Async SQLAlchemy, Alembic, and PostgreSQL-backed tests.
- Authentication foundation with users, refresh sessions, API tokens, routes, and CI coverage.

## Documentation policy

- Keep one primary file per topic.
- Prefer short pointer docs over repeated guidance.
- Move reusable process guidance to the external playbook repo.
- Keep repository docs practical and current; delete or shrink stale prose instead of layering new prose on top.
