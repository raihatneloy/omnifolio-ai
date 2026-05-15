"""
Omnifolio AI — FastAPI Application

Entry point for the backend API server.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    # Startup: connect to DB, Redis, etc.
    yield
    # Shutdown: close connections


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.is_development,
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}