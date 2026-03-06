# Reports foundation knowledge pack

## Goal
Implement initial reporting endpoints for BDR/P&L and BDDS/cashflow based on the transaction model.

## Scope
- report query schemas
- service layer for aggregation
- endpoints for BDR and BDDS
- grouping by date and category at minimum
- tests for basic aggregation correctness

## Core rules
- BDR uses `date_accrual`.
- BDDS uses `date_cash`.
- Money calculations must stay in Decimal all the way to serialization.
- Keep report query logic in services/repositories, not routes.
- Support date filtering.

## Suggested endpoints
- `GET /api/v1/reports/pnl`
- `GET /api/v1/reports/cashflow`

## Minimum query support
- `from_date`
- `to_date`
- optional `group_by` with at least `day`, `month`, `category`

## Output expectations
- totals by group
- overall total in response when useful
- stable response schema suitable for a later frontend

## Do not do
- Do not add charting responsibilities to backend.
- Do not hard-code category names in aggregation logic.
- Do not use floats in aggregation.

## Tests
- P&L groups by accrual date.
- Cashflow groups by cash date.
- Date filtering works.
- Empty range returns valid empty response.
