"""Tests for the skill catalog workflow (create, read, update, delete, search)."""
from __future__ import annotations

import uuid

from httpx import AsyncClient

SKILL_PAYLOAD = {
    "name": "explain-code",
    "description": "Explains selected code in natural language",
    "harness": "claude-code",
    "command": "cat @selection | python3 -m lumen.explain",
    "category": "documentation",
    "tags": ["explanation", "code-review"],
    "version": "1.0.0",
}

SKILL_PAYLOAD_2 = {
    "name": "security-scan",
    "description": "Scans configs for secrets",
    "harness": "codex",
    "command": "lumen-scan @config",
    "category": "security",
    "tags": ["security", "linting"],
    "is_active": False,
    "version": "1.1.0",
}


async def test_create_skill(client: AsyncClient) -> None:
    """Creating a skill returns the persisted record with an ID."""
    resp = await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == SKILL_PAYLOAD["name"]
    assert data["harness"] == "claude-code"
    assert data["command"] == SKILL_PAYLOAD["command"]
    assert data["category"] == "documentation"
    assert data["tags"] == ["explanation", "code-review"]
    assert data["is_active"] is True
    assert data["version"] == "1.0.0"
    assert uuid.UUID(data["id"])  # valid UUID
    assert "created_at" in data
    assert "updated_at" in data


async def test_create_skill_invalid_name(client: AsyncClient) -> None:
    """Empty name returns 422."""
    payload = {**SKILL_PAYLOAD, "name": ""}
    resp = await client.post("/api/v1/skills", json=payload)
    assert resp.status_code == 422


async def test_create_skill_extra_fields_rejected(client: AsyncClient) -> None:
    """Extra fields in create payload are rejected."""
    payload = {**SKILL_PAYLOAD, "unexpected": "value"}
    resp = await client.post("/api/v1/skills", json=payload)
    assert resp.status_code == 422


async def test_create_skill_empty_command_rejected(client: AsyncClient) -> None:
    """Empty command returns 422."""
    payload = {**SKILL_PAYLOAD, "command": ""}
    resp = await client.post("/api/v1/skills", json=payload)
    assert resp.status_code == 422


async def test_get_skill_by_id(client: AsyncClient) -> None:
    """Retrieving a skill by ID returns the full record."""
    resp = await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    skill_id = resp.json()["id"]

    resp = await client.get(f"/api/v1/skills/{skill_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == skill_id
    assert data["name"] == SKILL_PAYLOAD["name"]


async def test_get_nonexistent_skill_returns_404(client: AsyncClient) -> None:
    """GET on a non-existent skill ID returns 404."""
    resp = await client.get(f"/api/v1/skills/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_list_skills_empty(client: AsyncClient) -> None:
    """Listing skills on an empty database returns empty list."""
    resp = await client.get("/api/v1/skills")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["per_page"] == 20


async def test_list_skills_pagination(client: AsyncClient) -> None:
    """Pagination returns correct page and total count."""
    for i in range(5):
        payload = {**SKILL_PAYLOAD, "name": f"skill-{i}"}
        await client.post("/api/v1/skills", json=payload)

    resp = await client.get("/api/v1/skills?page=1&per_page=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert len(data["items"]) == 2
    assert data["pages"] == 3

    resp = await client.get("/api/v1/skills?page=2&per_page=2")
    data = resp.json()
    assert len(data["items"]) == 2


async def test_list_skills_filter_by_harness(client: AsyncClient) -> None:
    """Filtering by harness returns only matching skills."""
    await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    await client.post("/api/v1/skills", json=SKILL_PAYLOAD_2)

    resp = await client.get("/api/v1/skills?harness=codex")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["harness"] == "codex"


async def test_list_skills_filter_by_category(client: AsyncClient) -> None:
    """Filtering by category returns matching skills."""
    await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    await client.post("/api/v1/skills", json=SKILL_PAYLOAD_2)

    resp = await client.get("/api/v1/skills?category=security")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["category"] == "security"


async def test_list_skills_filter_by_active(client: AsyncClient) -> None:
    """Filtering by is_active returns correct subsets."""
    await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    await client.post("/api/v1/skills", json=SKILL_PAYLOAD_2)

    resp = await client.get("/api/v1/skills?is_active=true")
    data = resp.json()
    assert len(data["items"]) == 1

    resp = await client.get("/api/v1/skills?is_active=false")
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "security-scan"


async def test_list_skills_search(client: AsyncClient) -> None:
    """Search matches name, description, and tags."""
    await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    await client.post("/api/v1/skills", json=SKILL_PAYLOAD_2)

    resp = await client.get("/api/v1/skills?search=security")
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "security-scan"

    resp = await client.get("/api/v1/skills?search=explain")
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "explain-code"


async def test_update_skill(client: AsyncClient) -> None:
    """Updating a skill modifies specified fields."""
    resp = await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    skill_id = resp.json()["id"]

    update = {"name": "explain-code-v2", "is_active": False, "tags": ["explain"]}
    resp = await client.put(f"/api/v1/skills/{skill_id}", json=update)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "explain-code-v2"
    assert data["is_active"] is False
    assert data["tags"] == ["explain"]
    # Unchanged fields preserved
    assert data["command"] == SKILL_PAYLOAD["command"]
    assert data["harness"] == "claude-code"



async def test_create_skill_version(client: AsyncClient) -> None:
    """Creating a skill version snapshots current state."""
    resp = await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    skill_id = resp.json()["id"]

    # Create a version
    resp = await client.post(
        f"/api/v1/skills/{skill_id}/versions",
        json={"version": "1.1.0", "created_by": "test-user"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["skill_id"] == skill_id
    assert data["version"] == "1.1.0"
    assert data["name"] == SKILL_PAYLOAD["name"]
    assert data["command"] == SKILL_PAYLOAD["command"]
    assert data["created_by"] == "test-user"
    assert "created_at" in data


async def test_create_duplicate_version_returns_400(client: AsyncClient) -> None:
    """Creating a duplicate version returns 400."""
    resp = await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    skill_id = resp.json()["id"]

    await client.post(
        f"/api/v1/skills/{skill_id}/versions",
        json={"version": "1.1.0"},
    )
    resp = await client.post(
        f"/api/v1/skills/{skill_id}/versions",
        json={"version": "1.1.0"},
    )
    assert resp.status_code == 400


async def test_create_version_nonexistent_skill_returns_404(client: AsyncClient) -> None:
    """Creating a version for non-existent skill returns 404."""
    resp = await client.post(
        f"/api/v1/skills/{uuid.uuid4()}/versions",
        json={"version": "1.1.0"},
    )
    assert resp.status_code == 404


async def test_list_skill_versions(client: AsyncClient) -> None:
    """Listing skill versions returns all versions newest first."""
    resp = await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    skill_id = resp.json()["id"]

    await client.post(
        f"/api/v1/skills/{skill_id}/versions",
        json={"version": "1.1.0"},
    )
    await client.post(
        f"/api/v1/skills/{skill_id}/versions",
        json={"version": "1.2.0"},
    )

    resp = await client.get(f"/api/v1/skills/{skill_id}/versions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3  # initial 1.0.0 + 1.1.0 + 1.2.0
    # Newest first
    assert data[0]["version"] == "1.2.0"
    assert data[1]["version"] == "1.1.0"
    assert data[2]["version"] == "1.0.0"

async def test_get_skill_version(client: AsyncClient) -> None:
    """Getting a specific skill version works."""
    resp = await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    skill_id = resp.json()["id"]

    await client.post(
        f"/api/v1/skills/{skill_id}/versions",
        json={"version": "1.1.0"},
    )

    resp = await client.get(f"/api/v1/skills/{skill_id}/versions/1.1.0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.1.0"
    assert data["skill_id"] == skill_id


async def test_get_nonexistent_version_returns_404(client: AsyncClient) -> None:
    """Getting a non-existent version returns 404."""
    resp = await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    skill_id = resp.json()["id"]

    resp = await client.get(f"/api/v1/skills/{skill_id}/versions/9.9.9")
    assert resp.status_code == 404


async def test_rollback_skill(client: AsyncClient) -> None:
    """Rolling back a skill restores previous version."""
    resp = await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    skill_id = resp.json()["id"]

    # Update the skill
    await client.put(
        f"/api/v1/skills/{skill_id}",
        json={"name": "updated-name", "command": "new command"},
    )

    # Create a version of the updated state
    await client.post(
        f"/api/v1/skills/{skill_id}/versions",
        json={"version": "2.0.0"},
    )

    # Rollback to original version (1.0.0 - the initial skill state)
    resp = await client.post(
        f"/api/v1/skills/{skill_id}/rollback",
        json={"version": "1.0.0"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == SKILL_PAYLOAD["name"]
    assert data["command"] == SKILL_PAYLOAD["command"]
    assert data["version"] == "1.0.0"


async def test_rollback_nonexistent_version_returns_404(client: AsyncClient) -> None:
    """Rolling back to non-existent version returns 404."""
    resp = await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    skill_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/skills/{skill_id}/rollback",
        json={"version": "9.9.9"},
    )
    assert resp.status_code == 404


async def test_rollback_nonexistent_skill_returns_404(client: AsyncClient) -> None:
    """Rolling back non-existent skill returns 404."""
    resp = await client.post(
        f"/api/v1/skills/{uuid.uuid4()}/rollback",
        json={"version": "1.0.0"},
    )
    assert resp.status_code == 404

async def test_update_nonexistent_skill_returns_404(client: AsyncClient) -> None:
    """PUT on a non-existent skill returns 404."""
    resp = await client.put(
        f"/api/v1/skills/{uuid.uuid4()}", json={"name": "new"}
    )
    assert resp.status_code == 404


async def test_delete_skill(client: AsyncClient) -> None:
    """Deleting a skill removes it from the catalog."""
    resp = await client.post("/api/v1/skills", json=SKILL_PAYLOAD)
    skill_id = resp.json()["id"]

    resp = await client.delete(f"/api/v1/skills/{skill_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/skills/{skill_id}")
    assert resp.status_code == 404


async def test_delete_nonexistent_skill_returns_404(client: AsyncClient) -> None:
    """DELETE on a non-existent skill returns 404."""
    resp = await client.delete(f"/api/v1/skills/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_harness_normalization(client: AsyncClient) -> None:
    """Harness aliases are normalized to valid enum values."""
    aliases = ["claude", "openai-code", "cursor", "claude_code"]
    for alias in aliases:
        payload = {**SKILL_PAYLOAD, "name": f"skill-{alias}"}
        resp = await client.post(
            "/api/v1/skills", json={**payload, "harness": alias}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["harness"] in {"claude-code", "codex", "cursor", "generic"}


async def test_tag_normalization_dedup(client: AsyncClient) -> None:
    """Tags are lowercased, stripped, and deduplicated."""
    payload = {
        **SKILL_PAYLOAD,
        "name": "tag-test",
        "tags": ["Review  ", "REVIEW", "review", "Explain"],
    }
    resp = await client.post("/api/v1/skills", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["tags"] == ["review", "explain"]