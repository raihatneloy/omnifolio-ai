"""
Omnifolio AI — Backend Configuration

Uses Pydantic BaseSettings to load environment variables with
sensible defaults. All secrets can be overridden via .env file.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "Omnifolio AI"
    APP_VERSION: str = "0.1.0"
    ENV: str = Field(default="development", pattern=r"^(development|production|test)$")
    SECRET_KEY: str = Field(default="dev-secret-change-me-in-production", min_length=8)

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://omnifolio:omnifolio@localhost:5432/omnifolio",
        description="PostgreSQL connection URL (asyncpg)",
    )

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # ── LLM ──────────────────────────────────────────────
    LLM_PROVIDER: str = Field(
        default="openrouter",
        description="Active LLM provider (openrouter, google, openai, anthropic)",
    )
    LLM_MODEL: str = Field(
        default="openai/gpt-4o-mini",
        description="Model ID on the chosen provider",
    )
    LLM_API_KEY: str = Field(default="", description="API key for the LLM provider")
    LLM_TEMPERATURE: float = Field(default=0.0, ge=0.0, le=2.0)
    LLM_MAX_TOKENS: int = Field(default=4096, gt=0)

    # ── CORS ─────────────────────────────────────────────
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3001", "http://localhost:3000"],
        description="Allowed CORS origins",
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def _validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql+asyncpg://", "postgresql://")):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg:// or postgresql://")
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def _warn_default_secret(cls, v: str) -> str:
        if v == "dev-secret-change-me-in-production":
            import warnings
            warnings.warn(
                "SECRET_KEY is using the default dev value. "
                "Set a real secret in production.",
                stacklevel=1,
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.ENV == "development"

    @property
    def is_test(self) -> bool:
        return self.ENV == "test"


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()