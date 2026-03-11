# Reports foundation knowledge pack

## Goal
Implement reporting endpoints for BDR/P&L and BDDS/cashflow, then extend reads
with unified ledger and forecast views over actual plus projected data.

## Scope
- report query schemas
- service layer for aggregation
- endpoints for BDR and BDDS
- unified cashflow ledger and forecast endpoints
- grouping by category/type at minimum
- tests for basic aggregation correctness

## Core rules
- BDR uses `date_accrual`.
- BDDS uses `date_cash`.
- Unified ledger reads combine actual transactions with pending/skipped projected transactions.
- Money calculations must stay in Decimal all the way to serialization.
- Keep report query logic in services/repositories, not routes.
- Support date filtering.
- Ledger balances are derived at read time, not persisted as transaction snapshots.

## Endpoints
- `GET /api/v1/reports/pnl`
- `GET /api/v1/reports/cashflow`
- `GET /api/v1/cashflow/report`
- `GET /api/v1/cashflow/forecast`

## Minimum query support
- `start_date` / `end_date` for report aggregations
- `from` / `to` for unified cashflow ledger
- `mode` for `mixed`, `actual_only`, or `planned_only` ledger reads
- `include_skipped` for optionally exposing skipped projections in unified ledger reads
- `target_date` for forecast horizon, defaulting to a near-term future window if omitted
- optional `group_by` with at least category/type in report endpoints

## Output expectations
- totals by group
- overall total in response when useful
- stable response schema suitable for a later frontend
- running/opening/closing balance in unified ledger responses
- unified rows include linkage fields such as `planned_payment_id`, `projected_transaction_id`, and `transaction_id`
- forecast summary exposes current balance, projected income/expense, projected balance, and pending count

## Do not do
- Do not add charting responsibilities to backend.
- Do not hard-code category names in aggregation logic.
- Do not use floats in aggregation.
- Do not persist a redundant balance snapshot when it can be derived at read time.

## Tests
- P&L groups by accrual date.
- Cashflow groups by cash date.
- Date filtering works.
- Empty range returns valid empty response.
- Updating actual transactions should affect the next ledger read automatically.
- Confirmed or skipped projections should affect unified cashflow reads according to mode and status rules.
