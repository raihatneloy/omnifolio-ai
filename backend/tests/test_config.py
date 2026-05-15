"""Tests for backend configuration and settings."""

import os
import warnings

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


class TestSettingsDefaults:
    """Test that settings load with correct defaults."""

    def test_default_env_is_development(self):
        os.environ.pop("ENV", None)
        settings = Settings()
        assert settings.ENV == "development"

    def test_default_llm_provider_is_openrouter(self):
        settings = Settings()
        assert settings.LLM_PROVIDER == "openrouter"

    def test_default_llm_model_is_gpt4o_mini(self):
        settings = Settings()
        assert settings.LLM_MODEL == "openai/gpt-4o-mini"

    def test_default_database_url(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        settings = Settings()
        assert "postgresql+asyncpg://" in settings.DATABASE_URL
        assert "omnifolio" in settings.DATABASE_URL

    def test_default_redis_url(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        settings = Settings()
        assert settings.REDIS_URL == "redis://localhost:6379/0"

    def test_default_secret_key_warns(self):
        os.environ.pop("SECRET_KEY", None)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            settings = Settings()
            assert "dev-secret-change-me" in settings.SECRET_KEY
            assert len(w) == 1
            assert "SECRET_KEY" in str(w[0].message)

    def test_default_temperature_is_zero(self):
        settings = Settings()
        assert settings.LLM_TEMPERATURE == 0.0

    def test_default_max_tokens(self):
        settings = Settings()
        assert settings.LLM_MAX_TOKENS == 4096

    def test_cors_origins_default(self):
        settings = Settings()
        assert "http://localhost:3001" in settings.CORS_ORIGINS
        assert "http://localhost:3000" in settings.CORS_ORIGINS


class TestSettingsValidation:
    """Test that settings validation works correctly."""

    def test_invalid_database_url_rejected(self):
        with pytest.raises(ValidationError):
            Settings(DATABASE_URL="sqlite:///test.db")

    def test_valid_postgres_url_accepted(self):
        settings = Settings(DATABASE_URL="postgresql://user:pass@host/db")
        assert "postgresql://" in settings.DATABASE_URL

    def test_valid_asyncpg_url_accepted(self):
        settings = Settings(DATABASE_URL="postgresql+asyncpg://user:pass@host/db")
        assert "postgresql+asyncpg://" in settings.DATABASE_URL

    def test_invalid_env_rejected(self):
        with pytest.raises(ValidationError):
            Settings(ENV="staging")

    def test_valid_envs_accepted(self):
        for env in ("development", "production", "test"):
            settings = Settings(ENV=env)
            assert settings.ENV == env

    def test_empty_llm_api_key_allowed(self):
        settings = Settings(LLM_API_KEY="")
        assert settings.LLM_API_KEY == ""

    def test_temperature_clamped(self):
        with pytest.raises(ValidationError):
            Settings(LLM_TEMPERATURE=-0.1)
        with pytest.raises(ValidationError):
            Settings(LLM_TEMPERATURE=2.1)

    def test_max_tokens_must_be_positive(self):
        with pytest.raises(ValidationError):
            Settings(LLM_MAX_TOKENS=0)


class TestSettingsProperties:
    """Test the is_production / is_development / is_test helpers."""

    def test_is_development(self):
        settings = Settings(ENV="development")
        assert settings.is_development is True
        assert settings.is_production is False
        assert settings.is_test is False

    def test_is_production(self):
        settings = Settings(ENV="production")
        assert settings.is_production is True
        assert settings.is_development is False
        assert settings.is_test is False

    def test_is_test(self):
        settings = Settings(ENV="test")
        assert settings.is_test is True
        assert settings.is_development is False
        assert settings.is_production is False


class TestGetSettings:
    """Test the cached settings singleton."""

    def test_get_settings_returns_settings_instance(self):
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2