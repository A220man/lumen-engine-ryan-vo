"""Session summary model for memory vault persistence."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class SessionSummary(Base):
    """A persisted session summary for memory vault continuous learning."""

    __tablename__ = "session_summaries"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(sa.String(255), nullable=False, unique=True, index=True)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True, index=True
    )
    summary_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    instinct_data: Mapped[str | None] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SessionSummary session={self.session_id} skill={self.skill_id}>"
