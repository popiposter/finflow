# CLAUDE.md

This file is intentionally short. It gives AI coding agents the minimum repository-specific contract and points them to the real source documents.

## Default workflow

1. Implement the feature.
2. Add unit or smoke tests only unless the task explicitly asks for heavier coverage.
3. Stop for review.
4. Add integration or API tests in a follow-up task.
5. Expand CI only when that heavier test layer is ready.

## Source documents

- Project overview: `README.md`
- Docs index: `docs/README.md`
- Testing rules: `docs/testing-architecture.md`
- Current scope and status: `IMPLEMENTATION.md`
- External process playbook: `https://github.com/popiposter/claude-github-dev-playbook`

## Repository constraints

- Do not add test-only sync database paths into runtime application code.
- Keep ORM models aligned with production migrations.
- Prefer config-driven auth lifetimes over hardcoded durations.
- Keep documentation compact and avoid duplicating the same rules across many files.
