"""
Review routes — approve/reject ingestion results.

Wired up in Phase 1 (Chunk 1.6).
"""

from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models import IngestionResult

router = APIRouter(prefix="/review", tags=["review"])


@router.get("", response_model=List[IngestionResult])
async def list_pending_reviews() -> List[IngestionResult]:
    """
    List all ingestion results awaiting review.

    ## Phase 1 (Chunk 1.6)
    Filter: needs_review=True.
    """
    # Stub — real DB query in Phase 1
    return []


@router.post("/confirm/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_review(result_id: str) -> None:
    """
    Confirm a reviewed ingestion result — write holdings to DB.

    ## Phase 1 (Chunk 1.6)
    """
    # Stub — real DB write in Phase 1
    pass


@router.post("/reject/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def reject_review(result_id: str) -> None:
    """
    Reject and discard an ingestion result.

    ## Phase 1 (Chunk 1.6)
    """
    # Stub — real DB delete in Phase 1
    pass