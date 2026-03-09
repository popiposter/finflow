# CLAUDE.md

This file is the short contract for AI coding agents working in FinFlow.

## Read first

1. `README.md`
2. `IMPLEMENTATION.md`
3. `backend/README.md`
4. `docs/testing-architecture.md` before changing tests, fixtures, or CI

## Delivery mode

- Implement the requested product stage with the smallest useful change set.
- Reuse existing domain model, repositories, schemas, and auth dependencies.
- Prefer updating existing source-of-truth docs instead of creating overlapping markdown files.
- Temporary session notes may be created under `.claude/`, but do not commit them.

## Local validation

Use the repo scripts:

```bash
./scripts/dev/check-backend.sh
./scripts/dev/assert-clean-git.sh
```

```powershell
./scripts/dev/check-backend.ps1
./scripts/dev/assert-clean-git.ps1
```

If you change Python code and Ruff is installed locally, run it manually before commit:

```bash
cd backend
ruff check .
ruff format .
```

Ruff is advisory, not a hard repo gate.

## Hard constraints

- Do not add test-only sync database paths into runtime application code.
- Keep ORM models aligned with production migrations.
- Prefer config-driven auth lifetimes over hardcoded durations.
- Do not use `git push --no-verify` in normal feature work.
- Treat GitHub checks as the source of truth after push.
