# PLAYBOOK.md

This file is only a local pointer.

## Shared source of truth

Reusable process guidance lives in the private repository:

- `popiposter/claude-github-dev-playbook`

## What remains local

Keep only FinFlow-specific deltas here:

- The testing contract lives in `docs/testing-architecture.md`.
- Backend CI keeps two layers: fast checks and DB-backed full-suite execution.
- Local rule files in `.claude/rules` must stay short and repository-specific.

Do not copy the external playbook back into this repository.
