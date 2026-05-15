"""
Transaction routes — CRUD for buy/sell/dividend events.

All responses and request bodies use Pydantic models from app.models.
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models import Transaction, TransactionBase, TransactionType

router = APIRouter(prefix="/transactions", tags=["transactions"])

# In-memory store for the skeleton. Replaced by DB in Phase 2.
_tx_store: dict[str, Transaction] = {}


@router.get("", response_model=List[Transaction])
async def list_transactions() -> List[Transaction]:
    """List all transactions."""
    return list(_tx_store.values())


@router.get("/{tx_id}", response_model=Transaction)
async def get_transaction(tx_id: str) -> Transaction:
    """Get a single transaction by ID."""
    if tx_id not in _tx_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return _tx_store[tx_id]


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(payload: TransactionBase) -> Transaction:
    """Create a new transaction."""
    tx = Transaction.model_construct(
        id=f"tx-{len(_tx_store) + 1}",  # temp id for skeleton; UUID in Phase 2
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **payload.model_dump(),
    )
    _tx_store[tx.id] = tx
    return tx


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(tx_id: str) -> None:
    """Delete a transaction."""
    if tx_id not in _tx_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    del _tx_store[tx_id]