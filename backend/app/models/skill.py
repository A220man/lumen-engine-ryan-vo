"""Skill domain model for agent harness capabilities."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class Harness(str, enum.Enum):
    """Supported agent harnesses."""

    CLAUDE_CODE = "claude-code"
    CODEX = "codex"
    OPENCODE = "opencode"
    CURSOR = "cursor"
    GENERIC = "generic"


class Skill(Base):
    """A reusable capability that can be loaded by an agent harness."""

    __tablename__ = "skills"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    harness: Mapped[str] = mapped_column(
        sa.String(50), nullable=False, default=Harness.GENERIC.value
    )
    command: Mapped[str] = mapped_column(sa.Text, nullable=False)
    category: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    tags: Mapped[list[str]] = mapped_column(sa.JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    version: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="1.0.0")
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
        return f"<Skill {self.name} harness={self.harness} v{self.version}>"