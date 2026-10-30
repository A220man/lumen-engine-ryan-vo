# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to Lumen Engine are documented here.

## [1.0.0] - 2026-10-16

### Added
- Backend FastAPI app with health and version endpoints
- Skill catalog CRUD: create, retrieve, list, update, delete skills
- Pagination, filtering by harness/category/is_active, and full-text search
- SQLite persistent storage via SQLAlchemy async engine
- Skill normalization: harness aliases (claude, openai-code → claude-code, codex), tag dedup/lowercase
- Skill validation: name/command max lengths, extra field rejection
- Pydantic request/response schemas with strict validation
- React + TypeScript + Vite frontend with skill catalog browser
- Skill list with pagination, search toolbar, and filter dropdown
- Skill detail view with command display, tags, and timestamps
- Skill creation form with inline validation
- Typed API client derived from backend routes
- 21 backend tests (pytest) covering CRUD, search, pagination, validation, 404s, normalization
- 3 frontend tests (vitest) covering empty state, skill listing, loading state
- Docker compose with backend, frontend, and Keycloak services
- Dockerfile for backend (nonroot, healthcheck) and frontend (multi-stage, nginx)
- CI workflow: backend tests, frontend tests, frontend build, Docker builds
- .env.example with all documented configuration variables