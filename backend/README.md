# FinFlow Backend

Personal finance system backend.

## Development

Install dependencies:
```bash
python -m pip install -e .[dev]
```

Run migrations:
```bash
alembic upgrade head
```

Run tests:
```bash
pytest
```

Run linter:
```bash
ruff check .
```

Type check:
```bash
mypy .
```

## Running the app

```bash
uvicorn app.main:app --reload
```
