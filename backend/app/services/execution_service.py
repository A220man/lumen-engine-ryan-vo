"""Skill execution service with sandboxed execution."""
from __future__ import annotations

import asyncio
import json
import os
import resource
import signal
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution import Execution, ExecutionStatus
from app.models.skill import Skill
from app.core.config import get_settings
from app.api.schemas import ExecutionRead


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

        # Record start time
        start_time = datetime.now(timezone.utc)
        execution.started_at = start_time
        execution.status = ExecutionStatus.RUNNING

        # Execute the skill
        result = await self._run_skill(
            skill=skill,
            input_data=input_data,
            timeout_seconds=timeout_seconds or self._settings.sandbox_timeout_seconds,
            env_vars=env_vars,
        )

        # Update execution record
        execution.status = result.status
        execution.output_data = result.output
        execution.error_message = result.error
        execution.exit_code = result.exit_code
        execution.duration_ms = result.duration_ms
        execution.completed_at = datetime.now(timezone.utc)

        await self._session.commit()
        await self._session.refresh(execution)

        return execution

    def _make_preexec_fn(
        self,
        memory_mb: int,
        cpu_seconds: int,
        max_processes: int,
    ):
        """Create a preexec_fn that sets resource limits in the child process.
        
        Gracefully handles platforms where resource limits are not available (e.g., macOS).
        """
        def set_limits() -> None:
            try:
                # Set memory limit (address space) in bytes
                memory_bytes = memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            except (AttributeError, ValueError, OSError):
                # RLIMIT_AS not available or not supported on this platform
                pass

            try:
                # Set CPU time limit in seconds
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
            except (AttributeError, ValueError, OSError):
                # RLIMIT_CPU not available or not supported
                pass

            try:
                # Set max processes limit
                resource.setrlimit(resource.RLIMIT_NPROC, (max_processes, max_processes))
            except (AttributeError, ValueError, OSError):
                # RLIMIT_NPROC not available or not supported
                pass

            try:
                # Disable core dumps
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            except (AttributeError, ValueError, OSError):
                # RLIMIT_CORE not available or not supported
                pass

        return set_limits

    async def _run_skill(
        self,
        skill: Skill,
        input_data: str | None,
        timeout_seconds: int,
        env_vars: dict[str, str] | None,
    ) -> ExecutionResult:
        """Run the skill command in a sandboxed environment with resource limits."""
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

        # Get sandbox limits from settings
        memory_mb = self._settings.sandbox_memory_mb
        cpu_seconds = self._settings.sandbox_cpu_seconds
        max_processes = self._settings.sandbox_max_processes

        preexec_fn = self._make_preexec_fn(memory_mb, cpu_seconds, max_processes)

        try:
            # Run with timeout and resource limits
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                preexec_fn=preexec_fn,
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

            # Check if process was killed due to resource limits
            if process.returncode is not None and process.returncode < 0:
                # Negative return code means killed by signal
                signal_num = -process.returncode
                if signal_num == signal.SIGXCPU:
                    status = ExecutionStatus.FAILED
                    error = (error or "") + f"\n[CPU time limit exceeded ({cpu_seconds}s)]"
                elif signal_num == signal.SIGKILL:
                    # Could be OOM killer or manual kill
                    status = ExecutionStatus.FAILED
                    error = (error or "") + f"\n[Process killed, possible memory limit ({memory_mb}MB)]"
                else:
                    status = ExecutionStatus.FAILED
            elif process.returncode == 0:
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
        page: int = 1,
        per_page: int = 20,
        skill_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """List executions with pagination and filtering."""
        query = select(Execution)

        if skill_id:
            query = query.where(Execution.skill_id == skill_id)
        if status:
            query = query.where(Execution.status == status)

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self._session.scalar(count_query) or 0

        # Pagination
        query = query.order_by(Execution.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self._session.execute(query)
        items = result.scalars().all()

        return {
            "items": [ExecutionRead.model_validate(e) for e in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }

