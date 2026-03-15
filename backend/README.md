# Backend

This folder contains the application code, migrations, and tests for the current FinFlow backend.

## Primary entry points

- `app/` — FastAPI application code.
- `alembic_migrations/` — schema migrations.
- `tests/` — unit, integration, and API tests.
- `pyproject.toml` — Python dependencies and tool configuration.

## Developer flow

- Implement feature code first.
- Add only the coverage required by the current stage.
- Use `docs/testing-architecture.md` before changing fixtures, DB setup, or CI expectations.
- Keep model definitions aligned with migrations.

## Local checks

Default local pass:

```bash
./scripts/dev/check-backend.sh
./scripts/dev/assert-clean-git.sh
```

The check script uses the uv-managed environment to match CI exactly. This ensures mypy and pytest run with the same tool versions and configuration as GitHub Actions.

If you touch Python code and Ruff is available locally, run it manually before commit:

```bash
cd backend
ruff check .
ruff format .
```

Ruff is advisory rather than a repo-enforced gate.

## Containerized local dev

The repo root contains a `compose.yml` that starts PostgreSQL, the backend, and the frontend together for local development.

Typical flow from the repo root:

```bash
docker compose up --build
```

The backend service:
- bind-mounts `backend/` for live reload
- runs `uv sync --extra dev` inside the container into an isolated named virtualenv volume
- applies `alembic upgrade head` before starting Uvicorn

Optional LLM parsing fallback can be enabled with:
- `OLLAMA_PARSE_ENABLED=true`
- `OLLAMA_API_KEY=...`
- `OLLAMA_API_BASE_URL=https://ollama.com/api`
- `OLLAMA_MODEL=gpt-oss:120b`

If you want to exercise the Telegram bot integration locally, provide:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`

The webhook endpoint is:

```text
POST /api/v1/integrations/telegram/webhook/{TELEGRAM_WEBHOOK_SECRET}
```

The current bot MVP supports:
- `/connect <api_token> [account_id]`
- `/status`
- `/disconnect`
- plain text transaction capture after linking

When dependencies change, restart the service or rerun `docker compose up --build`. When only Python source changes, `--reload` picks them up automatically.

## Practical lessons

- Do not commit temporary `.claude/session-*.md` notes.
- For repository `update()` methods that expose refreshed ORM state, prefer returning a fresh re-read when async session state gets tricky.
- For transaction tests, validate both `date_accrual` and `date_cash` in realistic scenarios rather than only same-day cases.
- For category APIs, validate parent ownership and hierarchy behavior explicitly.
