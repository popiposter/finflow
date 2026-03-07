# Documentation map

Use this index to find the single best document for each topic.

## Project and status

- `README.md` — project overview and navigation.
- `IMPLEMENTATION.md` — current implemented scope and likely next steps.

## Agent and process guidance

- `CLAUDE.md` — short repo contract for AI agents.
- `PLAYBOOK.md` — pointer to the shared private playbook.
- `.claude/README.md` — how local Claude docs are organized.
- `.claude/rules/README.md` — how to keep local rule files narrow and current.

## Engineering guidance

- `backend/README.md` — backend developer entry point.
- `docs/testing-architecture.md` — source of truth for tests, fixtures, and CI expectations.
- `.github/README.md` — GitHub automation scope only.

## Anti-duplication rule

If guidance is reusable across repositories, keep it in the external playbook repo.
If guidance is specific to FinFlow behavior, tests, or CI, keep it in this repository.
If two local docs say nearly the same thing, shorten one into a pointer.
