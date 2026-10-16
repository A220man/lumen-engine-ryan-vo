"""Skill service: business logic for the skill catalog workflow."""
from __future__ import annotations

import uuid
from typing import Any
from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Harness, Skill
from app.api.schemas import SkillCreate, SkillRead, SkillUpdate


class SkillService:
    """Service layer for skill CRUD and search operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, payload: SkillCreate) -> SkillRead:
        """Create a new skill and return the persisted record."""
        harness_value = self._normalize_harness(payload.harness)
        tags = self._normalize_tags(payload.tags)
        skill = Skill(
            name=payload.name,
            description=payload.description,
            harness=harness_value,
            command=payload.command,
            category=payload.category,
            tags=tags,
            is_active=payload.is_active,
            version=payload.version,
        )
        self._session.add(skill)
        await self._session.commit()
        await self._session.refresh(skill)
        return SkillRead.model_validate(skill)

    async def get(self, skill_id: uuid.UUID) -> SkillRead | None:
        """Retrieve a single skill by ID."""
        skill = await self._session.get(Skill, skill_id)
        if skill is None:
            return None
        return SkillRead.model_validate(skill)

    async def list(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        harness: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """List skills with pagination, filtering, and search."""
        stmt = select(Skill)
        if harness:
            stmt = stmt.where(Skill.harness == self._normalize_harness(harness))
        if category:
            stmt = stmt.where(Skill.category == category)
        if is_active is not None:
            stmt = stmt.where(Skill.is_active == is_active)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                (Skill.name.ilike(pattern))
                | (Skill.description.ilike(pattern))
                | (cast(Skill.tags, String).ilike(pattern))
            )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await self._session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Skill.created_at.desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        result = await self._session.execute(stmt)
        skills = [SkillRead.model_validate(s) for s in result.scalars().all()]

        return {
            "items": skills,
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "pages": (total_count + per_page - 1) // per_page if per_page else 0,
        }

    async def update(
        self, skill_id: uuid.UUID, payload: SkillUpdate
    ) -> SkillRead | None:
        """Update an existing skill. Returns None if not found."""
        skill = await self._session.get(Skill, skill_id)
        if skill is None:
            return None

        data = payload.model_dump(exclude_unset=True)
        if "harness" in data:
            data["harness"] = self._normalize_harness(data["harness"])
        if "tags" in data:
            data["tags"] = self._normalize_tags(data["tags"])

        for field, value in data.items():
            setattr(skill, field, value)

        await self._session.commit()
        await self._session.refresh(skill)
        return SkillRead.model_validate(skill)

    async def delete(self, skill_id: uuid.UUID) -> bool:
        """Delete a skill. Returns True if deleted, False if not found."""
        skill = await self._session.get(Skill, skill_id)
        if skill is None:
            return False
        await self._session.delete(skill)
        await self._session.commit()
        return True

    @staticmethod
    def _normalize_harness(value: str) -> str:
        """Normalize a harness string to a valid enum value."""
        value = value.lower().strip()
        try:
            return Harness(value).value
        except ValueError:
            # Map common aliases
            aliases = {
                "claude": Harness.CLAUDE_CODE.value,
                "claude_code": Harness.CLAUDE_CODE.value,
                "claudecode": Harness.CLAUDE_CODE.value,
                "openai-code": Harness.CODEX.value,
                "openai": Harness.CODEX.value,
            }
            return aliases.get(value, Harness.GENERIC.value)

    @staticmethod
    def _normalize_tags(tags: list[str]) -> list[str]:
        """Normalize tags: lowercase, strip, deduplicate, limit length."""
        seen: set[str] = set()
        result: list[str] = []
        for tag in tags:
            cleaned = tag.strip().lower()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
        return result[:20]