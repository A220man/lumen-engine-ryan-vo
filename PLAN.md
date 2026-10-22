# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skill-engine

## Roadmap

### core-skeleton — Core FastAPI/React Skeleton with Auth & Database

Status: done

Acceptance:
- FastAPI app starts and serves health endpoint
- React frontend builds and loads
- SQLite database with migrations works
- Basic tests pass

Implementation: `backend/app/main.py`, `backend/app/api/routes.py`, `backend/app/api/schemas.py`, `backend/app/models/skill.py`, `backend/app/services/skill_service.py`, `backend/app/core/database.py`, `backend/app/core/config.py`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/components/SkillList.tsx`, `frontend/src/pages/SkillCatalog.tsx`, `frontend/src/pages/SkillDetail.tsx`, `frontend/src/index.css`

Tests: `backend/tests/test_health.py`, `backend/tests/test_skills.py`, `backend/tests/conftest.py`, `frontend/src/pages/SkillCatalog.test.tsx`

### skill-engine — Skill Execution Engine

Status: in_progress

Acceptance:
- Skills can be defined, stored, and executed
- Skill registry with versioning
- Execution sandbox with timeout/resource limits
- API for skill CRUD and execution

### memory-vault — Memory Vault & Continuous Learning

Status: planned

Acceptance:
- Session summaries persisted
- Instinct extraction from sessions
- Cross-harness memory search/recall
- Memory vault API and UI

### security-scanner — AgentShield Security Scanner Integration

Status: planned

Acceptance:
- Scan agent configs for vulnerabilities
- Secrets detection in prompts/hooks/MCP
- Permission auditing
- CI/CD integration ready

### harness-adapters — Multi-Harness Adapter System

Status: planned

Acceptance:
- Claude Code plugin manifest generation
- Codex plugin manifest generation
- Cursor/OpenCode adapter configs
- Unified skill/agent format

### dashboard-ui — Developer Dashboard UI

Status: planned

Acceptance:
- Skill browser and execution UI
- Memory vault explorer
- Security scan results viewer
- Harness adapter status

