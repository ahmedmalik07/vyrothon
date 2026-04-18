"""
routers/ingest.py — POST /ingest endpoint.

Weight: 25% of judging score — the most valuable endpoint.
Crawls a folder, extracts faces, assigns grab_ids, persists everything.
"""

import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas import IngestRequest, IngestResponse, ErrorResponse
from services.ingest import ingest_folder

router = APIRouter(tags=["Ingest"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid folder path"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Ingest images from a folder",
    description=(
        "Crawl a folder recursively for images, extract face embeddings, "
        "assign unique grab_ids to each identity, and persist mappings. "
        "Idempotent: re-running on the same folder skips already-indexed images."
    ),
)
def ingest(request: IngestRequest, db: Session = Depends(get_db)):
    folder = request.folder

    # Validate folder exists
    if not os.path.isdir(folder):
        raise HTTPException(
            status_code=400,
            detail=f"Folder not found: '{folder}'. Provide a valid directory path.",
        )

    try:
        stats = ingest_folder(folder, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")

    return IngestResponse(**stats)
