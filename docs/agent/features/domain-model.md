# Domain model knowledge pack

## Goal
Implement the first core finance domain schema for FinFlow.

## Scope
- accounts
- categories
- transactions
- planned payments (schema only if needed for dependency wiring)
- shared enums and money/date conventions
- Alembic migration(s)
- repository scaffolding where helpful

## Required design rules
- Money uses Decimal in Python and NUMERIC in PostgreSQL.
- Datetimes are timezone-aware; pure business dates use DATE where appropriate.
- Separate `date_accrual` and `date_cash` on transactions.
- Keep transfer support possible even if transfer endpoints come later.
- Categories should support hierarchy via nullable parent_id.
- Accounts must support at least: cash, debit_card, credit_card, savings, other.

## Minimum tables in this milestone
- `accounts`
- `categories`
- `transactions`

## Suggested transaction fields
- `id`
- `user_id`
- `type`
- `account_id`
- `to_account_id` nullable
- `category_id` nullable
- `amount`
- `currency`
- `date_accrual`
- `date_cash`
- `description`
- `merchant`
- `source`
- `is_planned`
- `is_recurring_instance`
- `planned_payment_id` nullable
- timestamps

## Do not do
- Do not implement parsing logic here.
- Do not mix ORM models with Pydantic schemas.
- Do not use float for money.
- Do not skip migration files.

## Tests
- Model/import smoke checks.
- Repository tests only if repositories are introduced.
- Migration sanity check if test harness already exists.

## Suggested implementation order
1. Add enums and shared conventions.
2. Add ORM models.
3. Add Alembic migration.
4. Add schemas if needed by next issue.
5. Add minimal tests.
