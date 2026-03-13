# Backend specification

## Domain scope
FinFlow backend supports:
- user authentication via login/password
- browser sessions with rotating JWT cookies
- long-lived API tokens for iOS Shortcut
- accounts, categories, transactions, planned-payment templates, and projected transactions
- parse-and-create ingestion from free-form text
- workbook import of actual transactions from `.xlsx`
- BDR/accrual and BDDS/cashflow reports
- unified cashflow ledger and forecast reads over actual plus projected data
- scheduler-backed recurring projection generation

## Current milestone
The backend foundation is in place through:
- finance CRUD for accounts, categories, and transactions
- projection-first planned payment lifecycle
- projected transaction confirmation/skip flow
- scheduler-backed projection generation
- reporting plus cashflow ledger/forecast
- refined parse-and-create ingestion coverage
- `.xlsx` transaction import into actual transactions
- normalized API error envelopes with stable error codes and field maps

## API surface
Main API groups under `/api/v1`:
- `/auth` for register/login/logout/profile and API tokens
- `/accounts`, `/categories`, `/transactions` for core finance CRUD
- `/transactions/parse-and-create` for free-form ingestion into persisted transactions
- `/transactions/import` for workbook-based bulk ingestion into persisted transactions
- `/planned-payments` for recurring template CRUD plus `POST /generate`
- `/projected-transactions` for listing, updating, confirming, and skipping projections
- `/reports/pnl` and `/reports/cashflow` for accrual/cash aggregations
- `/cashflow/report` and `/cashflow/forecast` for unified read models
- `/health` and `/health/scheduler` for runtime status

## Lifecycle model
- `planned_payments` are reusable recurring templates.
- Scheduler or `POST /api/v1/planned-payments/generate` creates pending `projected_transactions`.
- Pending projections can be edited, confirmed into actual `transactions`, or skipped.
- Confirmed transactions keep `projected_transaction_id`; `planned_payment_id` remains audit linkage only.
- Unified cashflow reads derive balances at read time instead of storing balance snapshots per row.

## Parse-and-create behavior
- Request body is `text`, required `account_id`, and optional `category_id`.
- Separate bulk-import flow accepts multipart form-data with required `account_id` and `.xlsx` file.
- Parser uses deterministic heuristics for amount, description, category hints, and simple income/refund inference.
- Ownership of account/category is validated against the authenticated user before persistence.
- If `category_id` is omitted, the service may auto-match a user category by detected category name.
- Workbook import reads the first sheet in `date / description / amount` order, infers income vs expense from the sign, and returns imported/skipped row summary.

## Conventions
- API prefix: `/api/v1`
- Primary response format: JSON
- Timezone-aware datetimes in UTC at API/storage boundary unless a field is explicitly date-only
- Decimal for money values
- Error responses use `{ "error": { "code", "message", "fields" } }` for both domain and validation failures
