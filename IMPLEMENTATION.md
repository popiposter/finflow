# IMPLEMENTATION.md

## Current phase

Backend feature foundation is in place: authentication, core finance domain, parse-and-create ingestion, planned payments, projected transactions, reporting Stage 1, and finance CRUD Stage 4 for accounts, categories, and transactions.

## Completed

- Backend project skeleton.
- FastAPI application factory and health endpoint.
- Settings management.
- Async SQLAlchemy and Alembic.
- PostgreSQL-backed tests and CI pipeline.
- Authentication foundation: `User`, `ApiToken`, `RefreshSession`, auth service, auth routes, and tests.
- Core finance domain: accounts, categories, transactions, repositories, schemas, and migrations.
- Transaction ingestion from free-form text with authenticated parse-and-create flow, stronger parser heuristics for multiple numbers/type inference, and API persistence coverage.
- Planned payments Stage 3: template-first model/CRUD semantics, projection-based lifecycle cleanup, and audit-only linkage from actual transactions.
- Projected transactions Stage 1: model with status lifecycle, forecast layer between planned payments and transactions, and API endpoints for projection management.
- Projection scheduler Stage 1: scheduled generation of pending projected transactions from planned-payment templates and scheduler health endpoint.
- Reporting Stage 1: `GET /api/v1/reports/pnl`, `GET /api/v1/reports/cashflow`, aggregation services, grouping support, and smoke coverage.
- Cashflow ledger Stage 1: `GET /api/v1/cashflow/report` and `GET /api/v1/cashflow/forecast` over actual + projected rows with running/opening/closing balance calculation at read time.
- Finance CRUD Stage 4: CRUD endpoints for accounts, categories, and transactions, plus PATCH editing for actual transactions and coverage that verifies ledger reads reflect corrections on the next request.
- Category hierarchy validation and accrual-vs-cash transaction behavior coverage.
- Compact repo docs and local developer scripts for repeatable validation.
- CI infrastructure improvements: Python 3.12, uv-managed dependencies, aligned local and CI toolchains.

## Next likely steps

- Reporting refinement after product feedback on response shapes and aggregation semantics.
- Transaction editing refinement only if product later needs broader mutable fields such as `type`.
- Additional API and integration coverage only where the roadmap explicitly calls for it.
- Product refinement based on future feedback, especially around optional default-account selection.
- Keep process guidance compact and prefer scripts plus docs over long ritual prompts.
