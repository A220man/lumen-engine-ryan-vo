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
class SkillVersionRead(BaseModel):
    """Skill version response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    skill_id: uuid.UUID
    version: str
    name: str
    description: str | None
    harness: str
    command: str
    category: str | None
    tags: list[str]
    is_active: bool
    created_at: datetime
    created_by: str | None


class SkillVersionCreate(BaseModel):
    """Fields to create a new skill version (for versioning an existing skill)."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(..., min_length=1, max_length=50)
    created_by: str | None = Field(default=None, max_length=100)


class SkillRollback(BaseModel):
    """Fields to rollback a skill to a previous version."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(..., min_length=1, max_length=50)

class ExecutionCreate(BaseModel):
    """Fields required to execute a skill."""

    input_data: str | None = Field(default=None, max_length=10000)
    timeout_seconds: int | None = Field(default=None, ge=1, le=300)
    env_vars: dict[str, str] | None = Field(default=None, max_length=50)


class ExecutionRead(BaseModel):
    """Execution response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    skill_id: uuid.UUID
    skill_version: str
    status: str
    input_data: str | None
    output_data: str | None
    error_message: str | None
    exit_code: int | None
    duration_ms: int | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None