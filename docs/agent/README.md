# Agent docs index

This directory is the local knowledge base for Claude Code.

## Usage order
1. Read `CLAUDE.md`.
2. Read `IMPLEMENTATION.md`.
3. Read relevant `.claude/rules/*.md` files.
4. Read the docs in this folder for the current task.
5. Only then search the web if a gap still exists.

## Purpose
These files reduce drift, avoid random framework choices, and keep implementation patterns stable across sessions.

## Expected maintenance rule
Whenever a feature introduces a reusable pattern, add or update a doc here so the next feature can be implemented without external research.

## Current packs
- `backend-stack.md`
- `backend-roadmap.md`
- `auth-patterns.md`
- `feature-delivery-checklist.md`
- `refactoring-playbook.md`
- `github-cli-setup.md`
- `issue-execution-playbook.md`
- `features/project-bootstrap.md`
- `features/auth-foundation.md`
- `features/domain-model.md`
- `features/transaction-ingestion.md`
- `features/planned-payments.md`
- `features/reports-foundation.md`
