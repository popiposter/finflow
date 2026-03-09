# IMPLEMENTATION.md

## Current phase

Backend feature foundation is in place: authentication, finance domain models, parse-and-create ingestion, planned payments, and Stage 1 reporting, with CI running fast static checks and the full backend test suite.

## Completed

- Backend project skeleton.
- FastAPI application factory and health endpoint.
- Settings management.
- Async SQLAlchemy and Alembic.
- PostgreSQL-backed tests and CI pipeline.
- Authentication foundation: `User`, `ApiToken`, `RefreshSession`, auth service, auth routes, and tests.
- Core finance domain: accounts, categories, transactions, repositories, schemas, and migrations.
- Transaction ingestion from free-form text with authenticated parse-and-create flow.
- Planned payments Stage 1: model, CRUD, recurring generation, source-linked generated transactions, and idempotency protection.
- Reporting Stage 1: `GET /api/v1/reports/pnl`, `GET /api/v1/reports/cashflow`, aggregation services, grouping support, and smoke coverage.
- Staged testing workflow documented for AI-assisted delivery.
- Local process hardening for AI-assisted development: repo scripts for backend checks, clean-tree verification, and compact guardrails in repo docs.
- Top-level repository docs reduced to a smaller source-of-truth structure.

## Next likely steps

- Review and refine the reporting response shapes and aggregation semantics after product feedback.
- Add integration and API coverage in follow-up stages where the roadmap explicitly calls for it.
- Decide the next product feature after the current reporting foundation, likely scheduler-facing planned-payment execution or broader finance CRUD/report refinement.
- Keep process guidance compact and push repeatable lessons into scripts and source-of-truth docs rather than long prompts.
