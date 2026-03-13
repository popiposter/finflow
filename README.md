# FinFlow

FinFlow is an installable finance workspace under active product development, with a FastAPI backend and a mobile-first React PWA frontend.

## Where to start

- `IMPLEMENTATION.md` — current delivery status and next likely product steps.
- `CLAUDE.md` — short working contract for AI coding agents.
- `backend/README.md` — backend-specific developer workflow.
- `docs/testing-architecture.md` — how tests and CI are structured.

## Current scope

- Authentication foundation.
- Finance domain models for accounts, categories, transactions, and planned payments.
- Parse-and-create transaction ingestion with refined parser heuristics and authenticated persistence coverage.
- Bulk actual-transaction import from `.xlsx` workbooks into a selected account.
- Planned payments Stage 3 (template-first CRUD and projection-based lifecycle cleanup).
- Projected transactions Stage 1 (forecast layer, lifecycle, confirmation/skip flow).
- Projection scheduler Stage 1 (daily projection generation and scheduler health endpoint).
- Reporting Stage 1 plus unified cashflow ledger and forecast endpoints.
- Finance CRUD Stage 4 for accounts, categories, and transactions, including partial editing for actual transactions.
- Frontend v1: React + TypeScript + Vite PWA with cookie-auth session restore, offline persisted reads via TanStack Query + IndexedDB, and mobile-first screens for auth, dashboard, transactions, plans, projections, reports, and settings.
- Unified API/frontend error handling: normalized backend error envelopes, localized client-side error interpretation, and a React error boundary fallback.

## Local developer workflow

Use the repo scripts for the default local pass:

```bash
./scripts/dev/check-backend.sh
./scripts/dev/assert-clean-git.sh
```

If you touch Python code and Ruff is available locally, run it manually before commit:

```bash
cd backend
ruff check .
ruff format .
```

Ruff is now advisory in the local workflow rather than enforced by repo scripts.

## Frontend quick start

The PWA lives in `frontend/` and expects the backend API on the same origin. In local development, Vite proxies `/api` to `http://127.0.0.1:8000`.

```bash
cd frontend
npm install
npm run dev
```

Frontend environment defaults:

```bash
VITE_API_BASE_URL=/api/v1
```

Frontend validation:

```bash
cd frontend
npm run typecheck
npm run test:run
npm run build
```

The PWA ships an installable app shell, offline read-through cache for successful queries, and blocks offline mutations in the UI rather than queueing them.

## Docker Dev Stack

For an isolated one-command local stack, use Docker Compose from the repo root:

```bash
docker compose up --build
```

PowerShell helper:

```powershell
./scripts/dev/up-local-stack.ps1
```

This starts:
- `db` on `localhost:5432`
- `backend` on `http://127.0.0.1:8000`
- `frontend` on `http://127.0.0.1:5173`

The compose stack is set up for active development:
- source directories are bind-mounted, so Python and Vite reload on code changes
- backend dependencies live in an isolated named volume
- frontend `node_modules` lives in an isolated named volume
- backend runs `alembic upgrade head` automatically on startup

Update rules during development:
- app code only changed: keep `docker compose up` running and reload will pick it up
- Python or npm dependencies changed: restart the affected service, or rerun `docker compose up --build`
- Dockerfile / compose config changed: rerun `docker compose up --build`
- want a clean dependency refresh: `docker compose down -v` and then `docker compose up --build`
