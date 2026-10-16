"""Pydantic schemas for skill API request/response payloads."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SkillBase(BaseModel):
    """Common fields for skill payloads."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    harness: str = Field(default="generic")
    command: str = Field(..., min_length=1, max_length=5000)
    category: str | None = Field(None, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=20)
    is_active: bool = True
    version: str = Field(default="1.0.0")


class SkillCreate(SkillBase):
    """Fields required to create a skill."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "explain-code",
                "description": "Explains selected code in natural language",
                "harness": "claude-code",
                "command": "cat @selection | python3 -m lumen.explain",
                "category": "documentation",
                "tags": ["explanation", "code-review"],
                "version": "1.0.0",
            }
        },
    )


class SkillUpdate(BaseModel):
    """Fields that can be updated on a skill (all optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    harness: str | None = Field(default=None)
    command: str | None = Field(default=None, min_length=1, max_length=5000)
    category: str | None = Field(default=None, max_length=100)
    tags: list[str] | None = Field(default=None, max_length=20)
    is_active: bool | None = Field(default=None)
    version: str | None = Field(default=None)


class SkillRead(SkillBase):
    """Skill response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime