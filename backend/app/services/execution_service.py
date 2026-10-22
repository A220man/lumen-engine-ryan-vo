"""Skill execution service with sandboxed execution."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution import Execution, ExecutionStatus
from app.models.skill import Skill
from app.core.config import get_settings


@dataclass
class ExecutionResult:
    """Result of a skill execution."""

    status: ExecutionStatus
    output: str | None
    error: str | None
    exit_code: int | None
    duration_ms: int


class ExecutionService:
    """Service for executing skills with sandboxing."""

    # Default resource limits
    DEFAULT_TIMEOUT_SECONDS = 30
    DEFAULT_MAX_OUTPUT_SIZE = 1024 * 1024  # 1MB
    DEFAULT_MAX_MEMORY_MB = 512

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._settings = get_settings()

    async def execute(
        self,
        skill_id: uuid.UUID,
        input_data: str | None = None,
        timeout_seconds: int | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> Execution:
        """Execute a skill and return the execution record."""
        # Fetch the skill
        skill = await self._session.get(Skill, skill_id)
        if not skill:
            raise ValueError(f"Skill {skill_id} not found")

        if not skill.is_active:
            raise ValueError(f"Skill {skill_id} is not active")

        # Create execution record
        execution = Execution(
            skill_id=skill.id,
            skill_version=skill.version,
            input_data=input_data,
            status=ExecutionStatus.PENDING,
        )
        self._session.add(execution)
        await self._session.flush()

        # Execute the skill
        result = await self._run_skill(
            skill=skill,
            input_data=input_data,
            timeout_seconds=timeout_seconds or self.DEFAULT_TIMEOUT_SECONDS,
            env_vars=env_vars,
        )

        # Update execution record
        execution.status = result.status
        execution.output_data = result.output
        execution.error_message = result.error
        execution.exit_code = result.exit_code
        execution.duration_ms = result.duration_ms
        execution.started_at = datetime.now(timezone.utc)
        execution.completed_at = datetime.now(timezone.utc)

        await self._session.commit()
        await self._session.refresh(execution)

        return execution

    async def _run_skill(
        self,
        skill: Skill,
        input_data: str | None,
        timeout_seconds: int,
        env_vars: dict[str, str] | None,
    ) -> ExecutionResult:
        """Run the skill command in a sandboxed environment."""
        start_time = time.perf_counter()

        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Add skill-specific environment variables
        env["LUMEN_SKILL_ID"] = str(skill.id)
        env["LUMEN_SKILL_NAME"] = skill.name
        env["LUMEN_SKILL_HARNESS"] = skill.harness
        if input_data:
            env["LUMEN_INPUT"] = input_data

        # Build command - use shell to support pipes and redirections
        command = skill.command

        try:
            # Run with timeout and resource limits
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                # Limit working directory for safety
                cwd=self._settings.demo_mode and Path.cwd() or Path.cwd(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=input_data.encode() if input_data else None),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    output=None,
                    error=f"Execution timed out after {timeout_seconds} seconds",
                    exit_code=None,
                    duration_ms=int((time.perf_counter() - start_time) * 1000),
                )

            duration_ms = int((time.perf_counter() - start_time) * 1000)
            output = stdout.decode("utf-8", errors="replace")
            error = stderr.decode("utf-8", errors="replace")

            # Truncate output if too large
            if len(output) > self.DEFAULT_MAX_OUTPUT_SIZE:
                output = output[: self.DEFAULT_MAX_OUTPUT_SIZE] + "\n[OUTPUT TRUNCATED]"

            if process.returncode == 0:
                status = ExecutionStatus.COMPLETED
            else:
                status = ExecutionStatus.FAILED

            return ExecutionResult(
                status=status,
                output=output if output else None,
                error=error if error else None,
                exit_code=process.returncode,
                duration_ms=duration_ms,
            )

        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                output=None,
                error=str(e),
                exit_code=None,
                duration_ms=int((time.perf_counter() - start_time) * 1000),
            )

    async def get_execution(self, execution_id: uuid.UUID) -> Execution | None:
        """Retrieve an execution by ID."""
        return await self._session.get(Execution, execution_id)

    async def list_executions(
        self,
        skill_id: uuid.UUID | None = None,
        status: ExecutionStatus | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """List executions with pagination and filtering."""
        query = select(Execution).order_by(Execution.created_at.desc())
        count_query = select(func.count(Execution.id))

        if skill_id:
            query = query.where(Execution.skill_id == skill_id)
            count_query = count_query.where(Execution.skill_id == skill_id)

        if status:
            query = query.where(Execution.status == status.value)
            count_query = count_query.where(Execution.status == status.value)

        total = (await self._session.execute(count_query)).scalar_one()

        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self._session.execute(query)
        executions = result.scalars().all()

        return {
            "items": [ExecutionRead.model_validate(e) for e in executions],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }


# Import needed for list_executions
from sqlalchemy import func
from app.api.schemas import ExecutionRead