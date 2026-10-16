"""Tests for the health and version endpoints."""
from __future__ import annotations

from httpx import AsyncClient


async def test_health_endpoint(client: AsyncClient) -> None:
    """Health endpoint returns 200 with app name and version."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["app"] == "lumen-engine"
    assert "version" in data


async def test_version_endpoint(client: AsyncClient) -> None:
    """Version endpoint returns the app version."""
    resp = await client.get("/api/v1/version")
    assert resp.status_code == 200
    assert "version" in resp.json()


async def test_unknown_endpoint_returns_404(client: AsyncClient) -> None:
    """Unknown routes return 404."""
    resp = await client.get("/api/v1/nonexistent")
    assert resp.status_code == 404