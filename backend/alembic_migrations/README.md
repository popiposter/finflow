# Alembic Migrations

This directory contains migration scripts for FinFlow's database schema.

## Structure

```
alembic_migrations/
├── env.py          # Alembic environment configuration
├── script.py.mako  # Template for new migrations
├── versions/       # Generated migration scripts
└── README.md
```

## Usage

### Create a new migration
```bash
alembic revision -m "description"
```

### Run migrations
```bash
alembic upgrade head
```

### Run migrations in downgrade mode
```bash
alembic downgrade -1
```

### Auto-generate migrations
```bash
alembic revision --autogenerate -m "description"
```

## Configuration

The Alembic environment is configured in `env.py`:
- Reads database URL from `app.core.config.settings.database_url`
- Uses async SQLAlchemy engine for migrations
