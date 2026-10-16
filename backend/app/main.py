"""FastAPI application factory for Lumen Engine."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.core.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize database on startup."""
    settings = get_settings()
    await init_db()
    if settings.debug:
        import structlog

        logger = structlog.get_logger(__name__)
        logger.info("lumen-engine started", environment=settings.environment)
    yield
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    This is the single entrypoint used by both Docker and local commands.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router, prefix="/api/v1")

    return app


# Module-level app instance for uvicorn
app = create_app()