"""Tests for session summary persistence."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


async def test_create_session_summary(client: AsyncClient) -> None:
    """Creating a session summary persists it and returns the record."""
    resp = await client.post(
        "/api/v1/session-summaries",
        json={
            "session_id": "test-session-001",
            "skill_id": None,
            "summary_text": "Test summary for memory vault persistence",
            "instinct_data": {"key": "value", "intent": "learn"},
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_id"] == "test-session-001"
    assert data["summary_text"] == "Test summary for memory vault persistence"
    assert data["instinct_data"] == {"key": "value", "intent": "learn"}
    assert isinstance(data["id"], str)
    assert len(data["id"]) > 0


async def test_get_session_summary(client: AsyncClient) -> None:
    """Retrieving a session summary by session ID works."""
    await client.post(
        "/api/v1/session-summaries",
        json={
            "session_id": "test-session-002",
            "summary_text": "Another test summary",
        },
    )
    resp = await client.get("/api/v1/session-summaries/test-session-002")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "test-session-002"
    assert data["summary_text"] == "Another test summary"


async def test_list_session_summaries(client: AsyncClient) -> None:
    """Listing session summaries returns created records."""
    await client.post(
        "/api/v1/session-summaries",
        json={"session_id": "session-A", "summary_text": "First summary"},
    )
    await client.post(
        "/api/v1/session-summaries",
        json={"session_id": "session-B", "summary_text": "Second summary"},
    )
    resp = await client.get("/api/v1/session-summaries")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    session_ids = {s["session_id"] for s in data}
    assert "session-A" in session_ids
    assert "session-B" in session_ids


async def test_update_session_summary(client: AsyncClient) -> None:
    """Updating a session summary modifies the record."""
    await client.post(
        "/api/v1/session-summaries",
        json={"session_id": "session-update", "summary_text": "Original text"},
    )
    resp = await client.put(
        "/api/v1/session-summaries/session-update",
        json={"summary_text": "Updated text"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary_text"] == "Updated text"
    resp = await client.get("/api/v1/session-summaries/session-update")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary_text"] == "Updated text"


async def test_delete_session_summary(client: AsyncClient) -> None:
    """Deleting a session summary removes it."""
    await client.post(
        "/api/v1/session-summaries",
        json={"session_id": "session-delete", "summary_text": "Will be deleted"},
    )
    resp = await client.delete("/api/v1/session-summaries/session-delete")
    assert resp.status_code == 204
    resp = await client.get("/api/v1/session-summaries/session-delete")
    assert resp.status_code == 404
