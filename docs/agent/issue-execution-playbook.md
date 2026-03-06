# Issue execution playbook

## How Claude should execute an issue
1. Read the issue body carefully.
2. Read `CLAUDE.md`, `IMPLEMENTATION.md`, `.claude/rules/*.md`, and the relevant file in `docs/agent/features/`.
3. Restate the plan before editing files.
4. Change the minimum number of files necessary.
5. Add tests in the same task.
6. Update docs if a reusable pattern appears.
7. Summarize files changed, tests, and remaining follow-ups.

## Branch naming
- `<issue-number>-short-kebab-name`

## Commit guidance
- Small commits by concern.
- Keep docs/tests close to the code change.

## PR guidance
- Link the issue.
- Explain validation steps.
- List deferred work explicitly.
