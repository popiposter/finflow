# Documentation map

Use this index to find the source of truth for each topic.

## Project docs

- `README.md` — project overview and quick navigation.
- `IMPLEMENTATION.md` — current status and near-term roadmap.
- `CLAUDE.md` — compact AI-agent contract.
- `PLAYBOOK.md` — pointer to the external reusable playbook.

## Technical docs

- `backend/README.md` — backend entry point.
- `docs/testing-architecture.md` — test layers, fixture strategy, and CI expectations.
- `.github/README.md` — GitHub automation scope.
- `.claude/README.md` — local Claude rules policy.
- `.claude/rules/README.md` — how to keep per-rule files small and non-duplicative.

## Maintenance rules

- Do not duplicate the same process guidance across `README.md`, `CLAUDE.md`, and playbook files.
- If a document is mostly navigation, keep it under one screen and turn it into an index.
- If a rule applies across products, keep it in the external playbook repository.
