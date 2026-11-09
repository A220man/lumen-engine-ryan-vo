# Changelog

## 1.5.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Fixed - Skill Execution Engine Improvements
- Fixed execution timestamp ordering: `started_at` now set before execution begins, `completed_at` after execution finishes
- Improved cross-platform compatibility of resource limits in sandbox (graceful handling on macOS/other platforms where RLIMIT_* may not be available)
- Increased default max processes limit from 50 to 200 to avoid "Cannot fork" errors in constrained environments
## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to Lumen Engine are documented here.

## [1.3.0] - 2026-11-06

### Added - Skill Execution Engine
- Skill execution with sandboxed subprocess isolation
- Resource limits: memory (RLIMIT_AS), CPU time (RLIMIT_CPU), process count (RLIMIT_NPROC)
- Configurable sandbox limits via environment variables (SANDBOX_MEMORY_MB, SANDBOX_CPU_SECONDS, SANDBOX_MAX_PROCESSES, SANDBOX_TIMEOUT_SECONDS)
- Execution history tracking with status, output, error, exit code, duration
- API endpoints for skill execution, execution listing with pagination/filtering, execution retrieval
- 15 execution tests covering success, failure, timeout, memory limits, CPU limits, pagination, filtering

### Changed
- Updated execution service to use configurable sandbox settings from config
- Updated pagination response to use `pages` key for consistency

## [1.0.0] - 2026-10-16

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