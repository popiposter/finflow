# Linting and type-checking snippet pack

## Tooling baseline
- Ruff handles linting and formatting.
- mypy handles static type checks.
- pre-commit runs fast checks locally.
- GitHub Actions enforces the same rules centrally.

## Execution strategy
- During implementation: run Ruff often.
- Before commit: rely on pre-commit hooks.
- Before PR and in CI: run Ruff, mypy, and tests.

## Config placement
- Put Ruff and mypy config in `backend/pyproject.toml`.
- Keep pre-commit config at repository root.

## Merge policy
A PR is not ready if linting, type checks, or required tests fail.
