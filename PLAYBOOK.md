# Playbook

## AI delivery workflow

Use this default workflow for Claude-driven implementation tasks:

1. Ship feature code first.
2. Add unit or smoke tests that validate the core path.
3. Stop and request review before building integration or API test scaffolding.
4. After review, run a separate explicit task for integration and API tests.
5. Update CI only when the heavier test layer is ready to be enforced.

## Why this exists

This repository optimizes for fast iteration with Claude Code and auto-push.
The expensive failure mode is not a small code defect; it is the agent spending hours growing an over-complex test harness before the feature direction is validated.

## Expectations for tasks

- Feature implementation tasks should say whether they stop at code plus unit or smoke coverage.
- Integration or API test tasks should reference `docs/testing-architecture.md`.
- If a task needs new services, containers, or CI dependencies, call that out explicitly.
- Prefer small follow-up tasks over one huge prompt that mixes feature design, review response, CI expansion, and heavy test infrastructure.

## Expectations for issues

When writing or refining implementation issues, split them into stages:

- Stage 1: feature behavior and minimal test proof.
- Stage 2: review-driven fixes.
- Stage 3: integration or API coverage.
- Stage 4: CI enforcement or workflow expansion.

That staging keeps issues actionable for AI agents and makes it clear when a task is allowed to stop.
