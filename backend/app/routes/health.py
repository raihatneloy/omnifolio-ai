"""
Health routes — liveness and readiness probes.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe — app is alive."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse)
async def ready() -> HealthResponse:
    """Readiness probe — app is ready to serve traffic."""
    return HealthResponse(status="ready")