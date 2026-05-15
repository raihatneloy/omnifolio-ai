"""
Upload routes — file ingestion stubs.

Actual pipeline wired up in Phase 1 (Chunks 1.3–1.5).
"""

from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models import IngestionResult

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=IngestionResult, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)) -> IngestionResult:
    """
    Upload a CSV or PDF file for ingestion.

    ## Phase 1 (Chunk 1.5)
    Wire to: file type detection → semantic mapper → validator.
    For now, returns a stub result with needs_review=True.
    """
    content_type = file.content_type or ""
    if content_type not in ("text/csv", "application/pdf") and not content_type.endswith("csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}. Only CSV and PDF are accepted.",
        )
    # Stub — real pipeline in Phase 1
    return IngestionResult.model_construct(
        success=False,
        message="Upload stub — pipeline not yet wired. See Chunk 1.5.",
        mappings=[],
        holdings=[],
        errors=[],
        needs_review=True,
    )


@router.get("/status/{job_id}", response_model=IngestionResult)
async def get_upload_status(job_id: str) -> IngestionResult:
    """
    Poll ingestion job status.

    ## Phase 1 (Chunk 1.5)
    Wire to Redis-backed job queue (Celery deferred).
    For now, returns a stub.
    """
    return IngestionResult.model_construct(
        success=False,
        message=f"Job {job_id}: status stub — pipeline not yet wired. See Chunk 1.5.",
        mappings=[],
        holdings=[],
        errors=[],
        needs_review=True,
    )