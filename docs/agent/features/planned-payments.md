# Planned payments knowledge pack

## Goal
Implement planning and recurring payment support so FinFlow can model future obligations and generate transaction instances safely.

## Scope
- planned payment model
- recurrence definition fields
- repository/service for planned payments
- CRUD endpoints for planned payments
- generation strategy for scheduled transaction instances
- idempotency protection for recurring generation
- tests for scheduling and duplicate prevention

## Core rules
- Keep recurrence rules simple for MVP: once, monthly, weekly, yearly.
- Store enough metadata to regenerate predictable future instances.
- Separate the template (`planned_payments`) from generated transactions.
- Generated transactions must reference the source planned payment.
- Repeated scheduler runs must not create duplicates.

## Recommended fields
- `id`
- `user_id`
- `account_id`
- `to_account_id` nullable
- `category_id` nullable
- `amount`
- `currency`
- `schedule_type`
- `schedule_params` JSON
- `start_date`
- `end_date` nullable
- `description`
- `is_active`
- timestamps

## Endpoints
- `POST /api/v1/planned-payments`
- `GET /api/v1/planned-payments`
- `GET /api/v1/planned-payments/{id}`
- `PATCH /api/v1/planned-payments/{id}`
- `DELETE /api/v1/planned-payments/{id}` (soft-delete or deactivate is acceptable if consistent)

## Generation strategy
- Provide a service that can generate due transaction instances for a date or date range.
- Prefer an explicit job/service entry point rather than hiding generation inside route logic.
- Persist deduplication signal, e.g. generated occurrence date or a stable occurrence key.

## Do not do
- Do not introduce a heavy cron framework unless needed.
- Do not embed recurrence math in routes.
- Do not allow duplicate generated transactions for the same occurrence.

## Tests
- Create planned payment.
- Update/deactivate planned payment.
- Generate one due occurrence.
- Re-running generation does not duplicate occurrence.
