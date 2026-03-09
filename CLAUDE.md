# CLAUDE.md

This file is the short contract for AI coding agents working in FinFlow. It should stay compact and never become a second playbook.

## Do first

1. Read `README.md` for repo navigation.
2. Read `IMPLEMENTATION.md` for current scope.
3. Read `docs/testing-architecture.md` before changing tests, fixtures, or CI.
4. Use `PLAYBOOK.md` only as a pointer to the shared private playbook repo.

## Default delivery mode

- Implement the feature first.
- Add unit or smoke tests only unless the task explicitly asks for heavier coverage.
- Stop for review.
- Add integration or API tests in a follow-up task.
- Expand CI only when that heavier layer is ready.

## Before pushing

**Use the repo scripts and keep the git tree clean:**

```bash
# Bash
./scripts/dev/check-backend.sh
./scripts/dev/assert-clean-git.sh
```

```powershell
# PowerShell
./scripts/dev/check-backend.ps1
./scripts/dev/assert-clean-git.ps1
```

If `pre-commit` or a formatter modifies files:
1. Review the diff.
2. `git add -A`
3. `git commit --amend --no-edit` (or a small follow-up commit)
4. Re-run the checks.

## Hard constraints

- Do not add test-only sync database paths into runtime application code.
- Keep ORM models aligned with production migrations.
- Prefer config-driven auth lifetimes over hardcoded durations.
- Prefer editing an existing source-of-truth doc over creating another overlapping markdown file.
- Do not push code that fails format check or linting.
- Do not use `git push --no-verify` in normal feature work.
- Treat GitHub checks as the source of truth after push.
