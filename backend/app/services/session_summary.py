"""Session summary service for memory vault persistence."""
from __future__ import annotations
from datetime import datetime, timezone

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session_summary import SessionSummary


class SessionSummaryService:
    """Service layer for session summary CRUD and search operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        session_id: str,
        skill_id: uuid.UUID | None,
        summary_text: str,
        instinct_data: dict[str, Any] | None = None,
    ) -> SessionSummary:
        """Create a new session summary and persist it."""
        skill_id_str: Optional[str] = None
        if skill_id is not None:
            skill_id_str = str(skill_id)

        summary = SessionSummary(
            id=uuid.uuid4(),
            session_id=session_id,
            skill_id=skill_id_str,
            summary_text=summary_text,
            instinct_data=instinct_data,
        )
        self._session.add(summary)
        await self._session.flush()
        return summary

    async def get(self, session_id: str) -> SessionSummary | None:
        """Retrieve a session summary by session ID."""
        result = await self._session.execute(
            select(SessionSummary).where(SessionSummary.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[SessionSummary]:
        """List all session summaries."""
        result = await self._session.execute(select(SessionSummary))
        return list(result.scalars().all())

    async def update(
        self,
        session_id: str,
        summary_text: str | None = None,
        instinct_data: dict[str, Any] | None = None,
    ) -> SessionSummary | None:
        """Update a session summary."""
        summary = await self.get(session_id)
        if summary is None:
            return None
        if summary_text is not None:
            summary.summary_text = summary_text
        if instinct_data is not None:
            summary.instinct_data = instinct_data
        summary.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return summary

    async def delete(self, session_id: str) -> bool:
        """Delete a session summary. Returns True if deleted."""
        summary = await self.get(session_id)
        if summary is None:
            return False
        await self._session.delete(summary)
        await self._session.flush()
        return True
