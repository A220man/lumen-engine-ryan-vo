"""Tests for skill execution workflow."""
from __future__ import annotations

import uuid
from httpx import AsyncClient
import pytest


async def test_execute_skill_success(client: AsyncClient) -> None:
    """Executing a skill with a simple command succeeds."""
    # Create a skill that echoes input
    create_resp = await client.post(
        "/api/v1/skills",
        json={
            "name": "echo-skill",
            "description": "Echoes input",
            "harness": "generic",
            "command": "cat",
            "category": "utility",
            "tags": ["echo"],
        },
    )
    assert create_resp.status_code == 201
    skill = create_resp.json()
    skill_id = skill["id"]

    # Execute the skill with input
    exec_resp = await client.post(
        f"/api/v1/skills/{skill_id}/execute",
        json={"input_data": "hello world"},
    )
    assert exec_resp.status_code == 200
    execution = exec_resp.json()
    assert execution["skill_id"] == skill_id
    assert execution["status"] == "completed"
    assert execution["output_data"] == "hello world"
    assert execution["exit_code"] == 0
    assert execution["duration_ms"] is not None
    assert execution["duration_ms"] > 0


async def test_execute_skill_no_input(client: AsyncClient) -> None:
    """Executing a skill without input works."""
    create_resp = await client.post(
        "/api/v1/skills",
        json={
            "name": "date-skill",
            "description": "Prints current date",
            "harness": "generic",
            "command": "date",
            "category": "utility",
        },
    )
    assert create_resp.status_code == 201
    skill_id = create_resp.json()["id"]

    exec_resp = await client.post(
        f"/api/v1/skills/{skill_id}/execute",
        json={},
    )
    assert exec_resp.status_code == 200
    execution = exec_resp.json()
    assert execution["status"] == "completed"
    assert execution["output_data"] is not None
    assert len(execution["output_data"]) > 0


async def test_execute_skill_failure(client: AsyncClient) -> None:
    """Executing a failing skill returns failed status."""
    create_resp = await client.post(
        "/api/v1/skills",
        json={
            "name": "fail-skill",
            "description": "Always fails",
            "harness": "generic",
            "command": "exit 1",
            "category": "utility",
        },
    )
    assert create_resp.status_code == 201
    skill_id = create_resp.json()["id"]

    exec_resp = await client.post(
        f"/api/v1/skills/{skill_id}/execute",
        json={},
    )
    assert exec_resp.status_code == 200
    execution = exec_resp.json()
    assert execution["status"] == "failed"
    assert execution["exit_code"] == 1


async def test_execute_skill_timeout(client: AsyncClient) -> None:
    """Executing a skill that times out returns timeout status."""
    create_resp = await client.post(
        "/api/v1/skills",
        json={
            "name": "sleep-skill",
            "description": "Sleeps for a while",
            "harness": "generic",
            "command": "sleep 10",
            "category": "utility",
        },
    )
    assert create_resp.status_code == 201
    skill_id = create_resp.json()["id"]

    exec_resp = await client.post(
        f"/api/v1/skills/{skill_id}/execute",
        json={"timeout_seconds": 1},
    )
    assert exec_resp.status_code == 200
    execution = exec_resp.json()
    assert execution["status"] == "timeout"
    assert "timed out" in (execution["error_message"] or "").lower()


async def test_execute_nonexistent_skill_returns_404(client: AsyncClient) -> None:
    """Executing a non-existent skill returns 404."""
    exec_resp = await client.post(
        f"/api/v1/skills/{uuid.uuid4()}/execute",
        json={},
    )
    assert exec_resp.status_code == 404


async def test_execute_inactive_skill_returns_404(client: AsyncClient) -> None:
    """Executing an inactive skill returns 404."""
    create_resp = await client.post(
        "/api/v1/skills",
        json={
            "name": "inactive-skill",
            "description": "Inactive skill",
            "harness": "generic",
            "command": "echo test",
            "is_active": False,
        },
    )
    assert create_resp.status_code == 201
    skill_id = create_resp.json()["id"]

    exec_resp = await client.post(
        f"/api/v1/skills/{skill_id}/execute",
        json={},
    )
    assert exec_resp.status_code == 404


async def test_list_skill_executions(client: AsyncClient) -> None:
    """Listing executions for a skill works."""
    create_resp = await client.post(
        "/api/v1/skills",
        json={
            "name": "list-exec-skill",
            "description": "For listing executions",
            "harness": "generic",
            "command": "echo test",
            "category": "utility",
        },
    )
    assert create_resp.status_code == 201
    skill_id = create_resp.json()["id"]

    # Execute multiple times
    for _ in range(3):
        await client.post(f"/api/v1/skills/{skill_id}/execute", json={})

    # List executions
    list_resp = await client.get(f"/api/v1/skills/{skill_id}/executions")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["per_page"] == 20


async def test_list_skill_executions_filter_by_status(client: AsyncClient) -> None:
    """Filtering executions by status works."""
    create_resp = await client.post(
        "/api/v1/skills",
        json={
            "name": "filter-exec-skill",
            "description": "For filtering executions",
            "harness": "generic",
            "command": "echo test",
            "category": "utility",
        },
    )
    assert create_resp.status_code == 201
    skill_id = create_resp.json()["id"]

    # Execute once successfully
    await client.post(f"/api/v1/skills/{skill_id}/execute", json={})

    # Execute once with failure
    create_resp2 = await client.post(
        "/api/v1/skills",
        json={
            "name": "fail-filter-skill",
            "description": "For filtering",
            "harness": "generic",
            "command": "exit 1",
            "category": "utility",
        },
    )
    skill_id2 = create_resp2.json()["id"]
    await client.post(f"/api/v1/skills/{skill_id2}/execute", json={})

    # Filter completed
    list_resp = await client.get(
        f"/api/v1/skills/{skill_id}/executions?status=completed"
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "completed"

    # Filter failed
    list_resp = await client.get(
        f"/api/v1/skills/{skill_id2}/executions?status=failed"
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "failed"
async def test_get_execution_by_id(client: AsyncClient) -> None:
    """Retrieving an execution by ID works."""
    create_resp = await client.post(
        "/api/v1/skills",
        json={
            "name": "get-exec-skill",
            "description": "For getting execution",
            "harness": "generic",
            "command": "cat",  # Echo stdin to stdout
            "category": "utility",
        },
    )
    assert create_resp.status_code == 201
    skill_id = create_resp.json()["id"]

    exec_resp = await client.post(
        f"/api/v1/skills/{skill_id}/execute", json={"input_data": "test input"}
    )
    assert exec_resp.status_code == 200
    execution = exec_resp.json()
    execution_id = execution["id"]

    # Get by ID
    get_resp = await client.get(f"/api/v1/executions/{execution_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == execution_id
    assert data["input_data"] == "test input"
    assert data["output_data"] == "test input"


async def test_get_nonexistent_execution_returns_404(client: AsyncClient) -> None:
    """GET on non-existent execution returns 404."""
    resp = await client.get(f"/api/v1/executions/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_execute_with_env_vars(client: AsyncClient) -> None:
    """Executing a skill with custom env vars works."""
    create_resp = await client.post(
        "/api/v1/skills",
        json={
            "name": "env-skill",
            "description": "Uses env var",
            "harness": "generic",
            "command": "echo $CUSTOM_VAR",
            "category": "utility",
        },
    )
    assert create_resp.status_code == 201
    skill_id = create_resp.json()["id"]

    exec_resp = await client.post(
        f"/api/v1/skills/{skill_id}/execute",
        json={"env_vars": {"CUSTOM_VAR": "custom_value"}},
    )
    assert exec_resp.status_code == 200
    execution = exec_resp.json()
    assert execution["status"] == "completed"
    assert "custom_value" in execution["output_data"]


async def test_execution_records_skill_version(client: AsyncClient) -> None:
    """Execution records the skill version at time of execution."""
    create_resp = await client.post(
        "/api/v1/skills",
        json={
            "name": "version-skill",
            "description": "Tests version recording",
            "harness": "generic",
            "command": "echo test",
            "version": "2.5.0",
        },
    )
    assert create_resp.status_code == 201
    skill = create_resp.json()
    skill_id = skill["id"]

    exec_resp = await client.post(f"/api/v1/skills/{skill_id}/execute", json={})
    assert exec_resp.status_code == 200
    execution = exec_resp.json()
    assert execution["skill_version"] == "2.5.0"


async def test_execution_pagination(client: AsyncClient) -> None:
    """Execution listing supports pagination."""
    create_resp = await client.post(
        "/api/v1/skills",
        json={
            "name": "page-skill",
            "description": "For pagination",
            "harness": "generic",
            "command": "echo test",
            "category": "utility",
        },
    )
    assert create_resp.status_code == 201
    skill_id = create_resp.json()["id"]

    # Execute 5 times
    for _ in range(5):
        await client.post(f"/api/v1/skills/{skill_id}/execute", json={})

    # Page 1 with 2 per page
    list_resp = await client.get(
        f"/api/v1/skills/{skill_id}/executions?page=1&per_page=2"
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["pages"] == 3

    # Page 2
    list_resp = await client.get(
        f"/api/v1/skills/{skill_id}/executions?page=2&per_page=2"
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert len(data["items"]) == 2
    assert data["page"] == 2

    # Page 3
    list_resp = await client.get(
        f"/api/v1/skills/{skill_id}/executions?page=3&per_page=2"
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert len(data["items"]) == 1
    assert data["page"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])