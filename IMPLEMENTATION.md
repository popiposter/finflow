# IMPLEMENTATION.md

## Current phase

Backend feature foundation is in place: authentication, core finance domain, parse-and-create ingestion, planned payments, projected transactions, reporting Stage 1, and finance CRUD Stage 3 for accounts, categories, and transactions.

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
- Projected transactions Stage 1: model with status lifecycle, forecast layer between planned payments and transactions, and API endpoints for projection management.
- Projection scheduler Stage 1: scheduled generation of pending projected transactions from planned payments, legacy execute flow wired to projections, and scheduler health endpoint.
- Reporting Stage 1: `GET /api/v1/reports/pnl`, `GET /api/v1/reports/cashflow`, aggregation services, grouping support, and smoke coverage.
- Finance CRUD Stage 3: CRUD endpoints for accounts, categories, and transactions, plus repository and API coverage.
- Category hierarchy validation and accrual-vs-cash transaction behavior coverage.
- Compact repo docs and local developer scripts for repeatable validation.
- CI infrastructure improvements: Python 3.12, uv-managed dependencies, aligned local and CI toolchains.

## Next likely steps

- Cashflow ledger report and forecast summary on top of actual + projected rows.
- Reporting refinement after product feedback on response shapes and aggregation semantics.
- Planned payments template cleanup now that recurring execution generates projections first.
- Additional API and integration coverage only where the roadmap explicitly calls for it.
- Keep process guidance compact and prefer scripts plus docs over long ritual prompts.
