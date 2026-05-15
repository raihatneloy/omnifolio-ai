"""Shared test fixtures and configuration."""

import os
import sys

# Ensure the backend directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.core.config import Settings


@pytest.fixture()
def settings() -> Settings:
    """Provide test settings with overridden values."""
    return Settings(
        ENV="test",
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test_db",
        REDIS_URL="redis://localhost:6379/1",
        SECRET_KEY="test-secret-key-for-testing-only",
        LLM_API_KEY="test-key",
    )


@pytest.fixture()
def test_settings_env(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_VERSION", raising=False)