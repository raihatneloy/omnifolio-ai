"""
Holdings routes — CRUD for investment holdings.

All responses and request bodies use Pydantic models from app.models.
"""

from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models import AssetType, Holding, HoldingBase

router = APIRouter(prefix="/holdings", tags=["holdings"])

# In-memory store for the skeleton. Replaced by DB in Phase 2.
_holdings_store: dict[str, Holding] = {}


@router.get("", response_model=List[Holding])
async def list_holdings() -> List[Holding]:
    """List all holdings."""
    return list(_holdings_store.values())


@router.get("/{holding_id}", response_model=Holding)
async def get_holding(holding_id: str) -> Holding:
    """Get a single holding by ID."""
    if holding_id not in _holdings_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")
    return _holdings_store[holding_id]


@router.post("", response_model=Holding, status_code=status.HTTP_201_CREATED)
async def create_holding(payload: HoldingBase) -> Holding:
    """Create a new holding."""
    holding = Holding.model_construct(
        id=payload.ticker,  # temp id for skeleton; UUID in Phase 2
        created_at=None,
        updated_at=None,
        **payload.model_dump(),
    )
    _holdings_store[holding.id] = holding
    return holding


@router.delete("/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holding(holding_id: str) -> None:
    """Delete a holding."""
    if holding_id not in _holdings_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")
    del _holdings_store[holding_id]