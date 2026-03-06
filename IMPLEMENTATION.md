# IMPLEMENTATION.md

## Current phase
Project bootstrap and architecture setup.

## Goals in progress
- [ ] Create backend project skeleton.
- [ ] Add pyproject.toml with approved dependencies.
- [ ] Add FastAPI application factory and health endpoint.
- [ ] Configure settings management.
- [ ] Configure async SQLAlchemy and Alembic.
- [ ] Implement authentication foundation.
- [ ] Add test infrastructure.
- [ ] Add reusable local knowledge packs for new features.

## Fixed decisions
- Backend is Python/FastAPI only.
- Database is PostgreSQL.
- ORM is async SQLAlchemy 2.x.
- Password hashing uses pwdlib.
- JWT uses PyJWT.
- Web auth uses HttpOnly Secure cookies.
- iOS Shortcut uses long-lived bearer API token stored hashed in DB.

## Agent workflow
- Before coding, Claude must read `CLAUDE.md`, `.claude/rules/*.md`, and relevant docs in `docs/agent/`.
- For each issue: create a short plan, implement in small steps, update docs when a new reusable pattern appears.
- Prefer local examples and snippets to web search.
- If using a new library or pattern, create or update a local note under `docs/agent/`.

## Next implementation checklist
1. Create `backend/pyproject.toml`.
2. Create `backend/app/main.py` and `backend/app/core/config.py`.
3. Create `backend/app/api/v1/health.py`.
4. Create app startup wiring and router registration.
5. Add test scaffolding with one health-check API test.
6. Only after scaffold is green, move to auth models and migrations.

## Done log
- [x] Repository initialized with Claude-oriented guidance files.
- [x] Added GitHub issue templates, PR template, and workflow placeholders.
- [x] Added local agent docs and reusable implementation playbooks.
