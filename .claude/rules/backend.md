# Backend development rules

- Async everywhere unless explicitly impossible.
- Keep route handlers thin.
- Services own business use-cases.
- Repositories own SQLAlchemy queries.
- Schemas are not ORM models.
- Money fields use Decimal, not float.
- Datetimes should be timezone-aware.
- Security and auth helpers belong in `app/core`.
