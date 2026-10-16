"""API routes for health check and skill catalog."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.schemas import SkillCreate, SkillRead, SkillUpdate
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.services.skill_service import SkillService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _get_skill_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SkillService:
    return SkillService(session)


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
    result = await service.list(
        page=page,
        per_page=per_page,
        harness=harness,
        category=category,
        is_active=is_active,
        search=search,
    )
    # Convert SkillRead models to dicts for response_model=dict
    result["items"] = [item.model_dump(mode="json") for item in result["items"]]
    return result


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
    return skill


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
    return skill


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