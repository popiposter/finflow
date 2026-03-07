# Rule folder notes

Use this folder only for small, repo-specific, operational rule files.

## Good rule files

A good rule file is:

- Narrow: one topic.
- Mechanical: easy for an agent to apply.
- Local: specific to FinFlow.
- Stable: unlikely to contradict `CLAUDE.md` or `docs/testing-architecture.md`.

## Good examples

- A FinFlow-only migration convention.
- A repository-specific path or naming invariant.
- A CI behavior unique to this codebase.

## Bad examples

- Repeating the full staged workflow.
- Rewriting testing architecture already documented elsewhere.
- Long essays that belong in `docs/` or the external playbook repo.

## Maintenance

When a rule becomes obsolete, update or delete it.
When a rule becomes general across products, move it to the private playbook repo.
