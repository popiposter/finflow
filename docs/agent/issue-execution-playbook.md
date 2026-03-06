# Issue execution playbook

## How Claude should execute an issue
1. Read the issue body carefully.
2. Retrieve issue context via GitHub CLI, not web fetch:
   - `gh issue view <number> --repo popiposter/finflow --json number,title,body,url`
3. Read `CLAUDE.md`, `IMPLEMENTATION.md`, `.claude/rules/*.md`, and the relevant file in `docs/agent/features/`.
4. Restate the plan before editing files.
5. Change the minimum number of files necessary.
6. Add tests in the same task.
7. Update docs if a reusable pattern appears.
8. Before finalizing, inspect `git status` and remove generated artifacts from the diff.
9. Summarize files changed, tests, CI reality, and remaining follow-ups.

## Branch naming
- `<issue-number>-short-kebab-name`

## Commit guidance
- Small commits by concern.
- Keep docs/tests close to the code change.
- Do not commit `__pycache__`, `*.pyc`, caches, or environment directories.

## PR guidance
- Link the issue.
- Explain validation steps.
- Distinguish local validation from CI validation.
- List deferred work explicitly.
