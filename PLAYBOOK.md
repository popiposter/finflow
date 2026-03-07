# PLAYBOOK.md

This file is a local pointer, not the full process manual.

## Source of truth

The main playbook now lives in the private repository:

- `popiposter/claude-github-dev-playbook`

## What stays local

Only repository-specific deltas should stay here:

- FinFlow uses the staged workflow from `docs/testing-architecture.md`.
- Backend CI must keep two layers: fast checks and DB-backed full-suite execution.
- Repo docs should stay compact; prefer pointers over duplicated process text.

If process guidance is broadly reusable across repositories, move it to the external playbook repo instead of expanding this file.
