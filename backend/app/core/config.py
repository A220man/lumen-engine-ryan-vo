"""Application configuration using pydantic-settings."""
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "lumen-engine"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./lumen.db"

    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT signing. MUST be set via SECRET_KEY in production.",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # OIDC / Keycloak (auth is a future milestone; disabled by default)
    oidc_enabled: bool = False
    oidc_issuer_url: str = "http://localhost:8080/realms/lumen"
    oidc_client_id: str = "lumen-engine"
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = "http://localhost:3000/callback"

    # LLM Providers
    llm_api_key: Optional[str] = None
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Demo mode (local only)
    demo_mode: bool = False
    demo_mode_bind_localhost: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()