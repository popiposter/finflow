# FinFlow

FinFlow is a finance backend under active product development.

## Where to start

- `IMPLEMENTATION.md` — current delivery status and next likely product steps.
- `CLAUDE.md` — short working contract for AI coding agents.
- `backend/README.md` — backend-specific developer workflow.
- `docs/testing-architecture.md` — how tests and CI are structured.

## Current backend scope

- Authentication foundation.
- Finance domain models for accounts, categories, transactions, and planned payments.
- Parse-and-create transaction ingestion.
- Planned payments Stage 1.
- Reporting Stage 1.
- Finance CRUD Stage 3 for accounts, categories, and transactions.

## Local developer workflow

Use the repo scripts for the default local pass:

```bash
./scripts/dev/check-backend.sh
./scripts/dev/assert-clean-git.sh
```

If you touch Python code and Ruff is available locally, run it manually before commit:

```bash
cd backend
ruff check .
ruff format .
```

Ruff is now advisory in the local workflow rather than enforced by repo scripts.
