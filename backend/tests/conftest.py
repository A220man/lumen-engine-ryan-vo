"""Test fixtures for Lumen Engine backend tests."""
from __future__ import annotations

from typing import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core import config
from app.core.database import close_db, init_db
from app.main import create_app


@pytest.fixture(autouse=True)
def _patch_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Patch settings to use test database and bypass OIDC."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-pytest")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("OIDC_ENABLED", "false")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_file}")
    # Clear lru_cache so new env values are picked up
    config.get_settings.cache_clear()
    # Reset database module globals so the engine is recreated with test URL
    from app.core import database

    database._engine = None
    database._session_factory = None


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """HTTP client with test database initialized."""
    app = create_app()
    await init_db()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        await close_db()