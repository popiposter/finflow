# .claude notes

This folder contains small local notes for Claude usage in FinFlow.

## Layout

- `.claude/README.md` — this file.
- `.claude/rules/README.md` — policy for rule-file design.
- `.claude/rules/*` — narrow repo-specific rules only.

## Keep local docs useful

- Prefer short instructions the agent can apply directly.
- Point to `CLAUDE.md` for the repo contract.
- Point to `docs/testing-architecture.md` for test and CI behavior.
- Point to the private playbook repo for reusable process guidance.

## Avoid

- Copying the same staged workflow into several files.
- Large narrative docs with no direct operational value.
- Rules that are generic across repositories.
