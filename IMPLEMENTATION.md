# IMPLEMENTATION.md

## Current phase

Backend feature foundation is in place, and the frontend now has a mobile-first PWA shell over the current API: authentication, core finance domain, parse-and-create ingestion, planned payments, projected transactions, reporting Stage 1, finance CRUD Stage 4, and an installable React client with offline persisted reads.

## Completed

- Backend project skeleton.
- FastAPI application factory and health endpoint.
- Settings management.
- Async SQLAlchemy and Alembic.
- PostgreSQL-backed tests and CI pipeline.
- Authentication foundation: `User`, `ApiToken`, `RefreshSession`, auth service, auth routes, and tests.
- Core finance domain: accounts, categories, transactions, repositories, schemas, and migrations.
- Transaction ingestion from free-form text with authenticated parse-and-create flow, stronger parser heuristics for multiple numbers/type inference, feature-flagged Ollama LLM fallback for ambiguous text, API persistence coverage, and `.xlsx` bulk import into actual transactions for a chosen account.
- Telegram bot ingestion: webhook-based chat linking through existing API tokens plus plain-text transaction capture into a selected account.
- Transaction ingestion from free-form text with authenticated parse-and-create flow, stronger parser heuristics for multiple numbers/type inference, feature-flagged Ollama LLM fallback for ambiguous text, API persistence coverage, and `.xlsx` bulk import into actual transactions for a chosen account.
- Telegram bot ingestion: webhook-based chat linking through existing API tokens plus plain-text transaction capture into a selected account.
- Planned payments Stage 3: template-first model/CRUD semantics, projection-based lifecycle cleanup, and audit-only linkage from actual transactions.
- Projected transactions Stage 1: model with status lifecycle, forecast layer between planned payments and transactions, and API endpoints for projection management.
- Projection scheduler Stage 1: scheduled generation of pending projected transactions from planned-payment templates and scheduler health endpoint.
- Reporting Stage 1: `GET /api/v1/reports/pnl`, `GET /api/v1/reports/cashflow`, aggregation services, grouping support, and smoke coverage.
- Cashflow ledger Stage 1: `GET /api/v1/cashflow/report` and `GET /api/v1/cashflow/forecast` over actual + projected rows with running/opening/closing balance calculation at read time.
- Finance CRUD Stage 4: CRUD endpoints for accounts, categories, and transactions, plus PATCH editing for actual transactions and coverage that verifies ledger reads reflect corrections on the next request.
- Category hierarchy validation and accrual-vs-cash transaction behavior coverage.
- Frontend v1 foundation: `frontend/` React + TypeScript + Vite workspace with cookie-auth session bootstrap, guarded routes, typed API clients, TanStack Query caching, IndexedDB persistence, and PWA manifest/service worker registration.
- Frontend product scope: login/register, dashboard, transactions, planned payments, projected transactions, cashflow/reporting views, and settings for accounts, categories, and profile/logout.
- Frontend validation and CI: Vitest component tests, production build, and dedicated frontend GitHub Actions job.
- Error handling hardening: normalized backend error envelopes, field-level validation mapping, localized frontend error rendering, localized client-side validation messages, and a root React error boundary.
- Containerized local dev stack: root `compose.yml`, backend/frontend dev Dockerfiles, and helper scripts for one-command startup with isolated dependencies and live reload.
- Compact repo docs and local developer scripts for repeatable validation.
- CI infrastructure improvements: Python 3.12, uv-managed dependencies, aligned local and CI toolchains.

## Next likely steps

- Frontend product refinement after real device feedback on navigation density, install UX, and dashboard/report ergonomics.
- Decide whether offline behavior should remain read-only or later grow into an explicit mutation queue as a separate phase.
- Reporting refinement after product feedback on response shapes and aggregation semantics.
- Transaction editing refinement only if product later needs broader mutable fields such as `type`.
- Additional API and integration coverage only where the roadmap explicitly calls for it.
- Product refinement based on future feedback, especially around optional default-account selection, richer chat-based ingestion UX, and LLM-assisted category/reporting workflows.
- Keep process guidance compact and prefer scripts plus docs over long ritual prompts.
