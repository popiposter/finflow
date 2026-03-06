# Repository hygiene rules

- Never commit generated Python artifacts: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`.
- Never commit local environments or machine-specific folders: `.venv/`, `venv/`, `.idea/`, `.vscode/`, `.DS_Store`.
- Before finalizing a task, inspect `git status` and remove generated files from the diff.
- Keep each branch scoped to the current issue unless explicit approval expands the scope.
- If validation was partial, say so clearly; do not imply CI passed when only local tests were run.
