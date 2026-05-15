"""
Omnifolio AI — FastAPI Application

Entry point for the backend API server.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.routes import health, holdings, review, transactions, upload

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


# ── Register routers ─────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(holdings.router)
app.include_router(transactions.router)
app.include_router(upload.router)
app.include_router(review.router)


# ── Health check (keepalive root) ────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Root health check — mirrors the /health endpoint for load balancer probes."""
    return {"status": "ok"}