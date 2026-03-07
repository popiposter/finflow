# Rule folder notes

Use this folder only for small, repository-specific rule files.

## Keep rules narrow

- One file, one topic.
- Prefer short operational constraints over large policy essays.
- Link to `CLAUDE.md`, `docs/testing-architecture.md`, or the external playbook instead of repeating them.

## Good examples

- Naming or path conventions unique to FinFlow.
- A repo-specific CI or migration constraint.
- A single workflow invariant that an AI agent can apply mechanically.

## Avoid

- Full copies of staged workflow guidance.
- Rewriting the same testing rules in multiple files.
- Long narrative docs that belong in `docs/`.
