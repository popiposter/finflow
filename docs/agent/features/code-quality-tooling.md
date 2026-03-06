# Code quality tooling knowledge pack

## Goal
Add modern Python quality tooling so FinFlow gets fast local feedback and reliable CI gating.

## Chosen tools
- Ruff for linting and formatting.
- mypy for type checking.
- pre-commit for local hooks.
- GitHub Actions for mandatory server-side validation.

## Rollout strategy
1. Add lint/type-check config.
2. Add local hook config.
3. Add CI workflow.
4. Make CI required for merge.

## Rules
- Fast checks should run often during implementation.
- pre-commit should run on changed files before commit.
- CI must re-run lint, format check, type check, and tests.
- Do not rely on CI alone; developers and agents should run checks locally during implementation.

## Recommended commands
- `pre-commit install`
- `pre-commit run --all-files`
- `ruff check backend`
- `ruff format backend`
- `mypy backend`
- `pytest backend/tests`

## Do not do
- Do not add multiple overlapping formatters.
- Do not add slow heavyweight linters unless there is a clear gap.
- Do not skip type checking for service/repository boundaries.

## Implementation notes
- Ruff and mypy config should live in `backend/pyproject.toml` once issue #1 creates it.
- CI workflow should become real after backend bootstrap lands.
- Treat lint/type/test failures as blocking for merge.
