# Planned payments knowledge pack

## Goal
Implement planned payments as recurring templates that generate projected
transactions first, while actual transactions remain downstream facts.

## Scope
- planned payment model
- recurrence definition fields
- repository/service for planned payments
- CRUD endpoints for planned payments
- generation strategy for scheduled projected instances
- idempotency protection for recurring generation
- scheduler-facing projection generation
- relationship with projected transaction confirmation flow
- tests for scheduling and duplicate prevention

## Core rules
- Keep recurrence rules simple: daily, weekly, monthly.
- Store enough metadata to generate predictable future projections.
- Treat `planned_payments` as a template layer, not the primary creator of
  actual transactions.
- Generated projected transactions must reference the source planned payment.
- Actual transactions may retain `planned_payment_id` only as audit/source
  linkage after a projection is confirmed.
- Repeated scheduler runs must not create duplicate projected occurrences.

## Current model shape
- `id`
- `user_id`
- `account_id`
- `category_id` nullable
- `amount`
- `recurrence`
- `start_date`
- `next_due_at`
- `end_date` nullable
- `description`
- `is_active`
- timestamps

## Endpoints
- `POST /api/v1/planned-payments`
- `GET /api/v1/planned-payments`
- `GET /api/v1/planned-payments/{id}`
- `PUT /api/v1/planned-payments/{id}`
- `DELETE /api/v1/planned-payments/{id}` (soft-delete or deactivate is acceptable if consistent)
- `POST /api/v1/planned-payments/generate`

## Generation strategy
- Provide a service that can generate due projected instances for a date.
- Scheduler-backed generation is the default production path.
- Prefer an explicit scheduler/service entry point rather than hiding generation inside route logic.
- Deduplicate by planned-payment plus occurrence date before inserting a new projection.
- Advance `next_due_at` after generation or after detecting an already-generated occurrence.

## Relationship to projections and actual transactions
- Each generated projection snapshots template values into `origin_*` fields and initializes editable `projected_*` fields.
- Planned payments do not directly create actual transactions anymore.
- Confirming a projection creates the actual transaction atomically downstream.
- `Transaction.planned_payment_id` may still be present for source tracing, but it is not the execution path.

## Do not do
- Do not introduce a heavy cron framework unless needed.
- Do not embed recurrence math in routes.
- Do not allow duplicate generated projections for the same occurrence.
- Do not reintroduce a direct planned-payment-to-transaction execution path.
- Do not document or re-add `POST /planned-payments/execute`; it is intentionally removed.

## Tests
- Create planned payment.
- Update/deactivate planned payment.
- Generate one due projected occurrence.
- Re-running generation does not duplicate occurrence.
- Scheduler/service generation preserves idempotency and advances the template cursor.
