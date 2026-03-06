# Migrations and DB snippet pack

## Async SQLAlchemy conventions
- Define declarative base in one place.
- Keep engine/session setup under `app/db/`.
- Models should be imported into metadata discovery from a central module.

## Alembic conventions
- One migration per logical change set.
- Migration filenames should be descriptive.
- Avoid mixing unrelated schema changes in one revision.
- Keep downgrade feasible whenever practical.

## Money fields
- Use `NUMERIC(14, 2)` or a consistent project-wide numeric precision.
- Expose as Decimal in Python.

## Dates
- Use `DATE` for business dates like `date_accrual` and `date_cash`.
- Use timezone-aware timestamps for audit columns.
