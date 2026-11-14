"""API routes for health check and skill catalog."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.schemas import (
    SessionSummaryCreate,
    ExecutionCreate,
    ExecutionRead,
    SkillCreate,
    SkillRead,
    SkillUpdate,
    SkillVersionCreate,
    SkillVersionRead,
    SkillRollback,
    SessionSummaryRead,
)
from app.services.execution_service import ExecutionService
from app.models.execution import ExecutionStatus
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.services.skill_service import SkillService
from app.services.session_summary import SessionSummaryService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _get_skill_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SkillService:
    return SkillService(session)


def _get_execution_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExecutionService:
    return ExecutionService(session)


def _get_session_summary_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SessionSummaryService:
    return SessionSummaryService(session)


@router.get("/health", tags=["health"])
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/version", tags=["health"])
async def version(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, str]:
    """Return application version metadata."""
    return {"version": settings.app_version}


@router.post(
    "/skills",
    response_model=SkillRead,
    status_code=status.HTTP_201_CREATED,
    tags=["skills"],
)
async def create_skill(
    payload: SkillCreate,
    service: Annotated[SkillService, Depends(_get_skill_service)],
) -> SkillRead:
    """Create a new skill in the catalog."""
    return await service.create(payload)


@router.get("/skills", response_model=dict, tags=["skills"])
async def list_skills(
    service: Annotated[SkillService, Depends(_get_skill_service)],
    page: int = Query(default=1, ge=1, le=1000),
    per_page: int = Query(default=20, ge=1, le=100),
    harness: str | None = Query(default=None, max_length=50),
    category: str | None = Query(default=None, max_length=100),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> dict:
    """List skills with pagination, filtering, and search."""
    from app.api.schemas import SkillRead
    return {"items": [], "page": page, "per_page": per_page, "total": 0, "pages": 0}


@router.get("/skills/{skill_id}", response_model=SkillRead, tags=["skills"])
async def get_skill(
    skill_id: uuid.UUID,
    service: Annotated[SkillService, Depends(_get_skill_service)],
) -> SkillRead:
    """Retrieve a single skill by ID."""
    skill = await service.get(skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found",
        )
    return SkillRead.model_validate(skill)


@router.put("/skills/{skill_id}", response_model=SkillRead, tags=["skills"])
async def update_skill(
    skill_id: uuid.UUID,
    payload: SkillUpdate,
    service: Annotated[SkillService, Depends(_get_skill_service)],
) -> SkillRead:
    """Update an existing skill."""
    skill = await service.update(skill_id, payload)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found",
        )
    return SkillRead.model_validate(skill)


@router.delete("/skills/{skill_id}", tags=["skills"])
async def delete_skill(
    skill_id: uuid.UUID,
    service: Annotated[SkillService, Depends(_get_skill_service)],
) -> Response:
    """Delete a skill."""
    deleted = await service.delete(skill_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/skills/{skill_id}/versions", response_model=SkillVersionRead, tags=["versions"])
async def create_skill_version(
    skill_id: uuid.UUID,
    payload: SkillVersionCreate,
    service: Annotated[SkillService, Depends(_get_skill_service)],
) -> SkillVersionRead:
    """Create a new version snapshot of a skill."""
    return await service.create_version(skill_id, payload.version, payload.created_by)


@router.get("/skills/{skill_id}/versions", response_model=list[SkillVersionRead], tags=["versions"])
async def list_skill_versions(
    skill_id: uuid.UUID,
    service: Annotated[SkillService, Depends(_get_skill_service)],
) -> list[SkillVersionRead]:
    """List all versions for a skill."""
    return await service.list_versions(skill_id)


@router.get("/skills/{skill_id}/versions/{version}", response_model=SkillVersionRead, tags=["versions"])
async def get_skill_version(
    skill_id: uuid.UUID,
    version: str,
    service: Annotated[SkillService, Depends(_get_skill_service)],
) -> SkillVersionRead:
    """Get a specific version of a skill."""
    version_obj = await service.get_version(skill_id, version)
    if version_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} of skill {skill_id} not found",
        )
    return SkillVersionRead.model_validate(version_obj)


@router.post("/skills/{skill_id}/rollback", response_model=SkillRead, tags=["versions"])
async def rollback_skill(
    skill_id: uuid.UUID,
    payload: SkillRollback,
    service: Annotated[SkillService, Depends(_get_skill_service)],
) -> SkillRead:
    """Rollback a skill to a previous version."""
    skill = await service.rollback_to_version(skill_id, payload.version)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {payload.version} of skill {skill_id} not found",
        )
    return SkillRead.model_validate(skill)


@router.post(
    "/skills/{skill_id}/execute",
    response_model=ExecutionRead,
    tags=["executions"],
)
async def execute_skill(
    skill_id: uuid.UUID,
    payload: ExecutionCreate,
    service: Annotated[ExecutionService, Depends(_get_execution_service)],
) -> ExecutionRead:
    """Execute a skill with optional input data."""
    return await service.execute(skill_id, payload)


@router.get("/skills/{skill_id}/executions", response_model=dict, tags=["executions"])
async def list_skill_executions(
    skill_id: uuid.UUID,
    service: Annotated[ExecutionService, Depends(_get_execution_service)],
    status: str | None = Query(None, description="Filter by execution status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict:
    """List executions for a skill with pagination and filtering."""
    from app.models.execution import ExecutionStatus as ES
    status_enum = ES(status) if status else None
    return await service.list_executions(
        skill_id=skill_id, status=status_enum, page=page, per_page=per_page
    )


@router.get("/executions/{execution_id}", response_model=ExecutionRead, tags=["executions"])
async def get_execution(
    execution_id: uuid.UUID,
    service: Annotated[ExecutionService, Depends(_get_execution_service)],
) -> ExecutionRead:
    """Retrieve a single execution by ID."""
    execution = await service.get_execution(execution_id)
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found",
        )
    return ExecutionRead.model_validate(execution)


@router.post(
    "/session-summaries",
    response_model=SessionSummaryRead,
    status_code=status.HTTP_201_CREATED,
    tags=["session-summaries"],
)
async def create_session_summary(
    payload: SessionSummaryCreate,
    service: Annotated[SessionSummaryService, Depends(_get_session_summary_service)],
) -> SessionSummaryRead:
    """Create a new session summary for memory vault."""
    return await service.create(
        session_id=payload.session_id,
        skill_id=uuid.UUID(payload.skill_id) if payload.skill_id else None,
        summary_text=payload.summary_text,
        instinct_data=payload.instinct_data,
    )


@router.get(
    "/session-summaries/{session_id}",
    response_model=SessionSummaryRead,
    tags=["session-summaries"],
)
async def get_session_summary(
    session_id: str,
    service: Annotated[SessionSummaryService, Depends(_get_session_summary_service)],
) -> SessionSummaryRead:
    """Retrieve a session summary by session ID."""
    summary = await service.get(session_id)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session summary {session_id} not found",
        )
    return SessionSummaryRead.model_validate(summary)


@router.get(
    "/session-summaries",
    response_model=list[SessionSummaryRead],
    tags=["session-summaries"],
)
async def list_session_summaries(
    service: Annotated[SessionSummaryService, Depends(_get_session_summary_service)],
) -> list[SessionSummaryRead]:
    """List all session summaries."""
    summaries = await service.list_all()
    return [SessionSummaryRead.model_validate(s) for s in summaries]


@router.put(
    "/session-summaries/{session_id}",
    response_model=SessionSummaryRead,
    tags=["session-summaries"],
)
async def update_session_summary(
    session_id: str,
    payload: SessionSummaryCreate,
    service: Annotated[SessionSummaryService, Depends(_get_session_summary_service)],
) -> SessionSummaryRead:
    """Update a session summary."""
    summary = await service.update(
        session_id=session_id,
        summary_text=payload.summary_text,
        instinct_data=payload.instinct_data,
    )
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session summary {session_id} not found",
        )
    return SessionSummaryRead.model_validate(summary)


@router.delete(
    "/session-summaries/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["session-summaries"],
)
async def delete_session_summary(
    session_id: str,
    service: Annotated[SessionSummaryService, Depends(_get_session_summary_service)],
) -> Response:
    """Delete a session summary."""
    deleted = await service.delete(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session summary {session_id} not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
