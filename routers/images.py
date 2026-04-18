"""
routers/images.py — GET /images/{grab_id} endpoint.

Retrieves all images associated with a given grab_id (person identity).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Image, ImageFace
from schemas import ImagesResponse, ImageInfo, ErrorResponse

router = APIRouter(tags=["Images"])


@router.get(
    "/images/{grab_id}",
    response_model=ImagesResponse,
    responses={
        404: {"model": ErrorResponse, "description": "No images found for this grab_id"},
    },
    summary="Get images by grab_id",
    description="Retrieve all images that contain the face associated with the given grab_id.",
)
def get_images(grab_id: UUID, db: Session = Depends(get_db)):
    records = (
        db.query(Image)
        .join(ImageFace, ImageFace.image_id == Image.id)
        .filter(ImageFace.grab_id == grab_id)
        .order_by(Image.created_at.desc())
        .all()
    )

    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"No images found for grab_id: {grab_id}",
        )

    return ImagesResponse(
        grab_id=str(grab_id),
        total_images=len(records),
        images=[
            ImageInfo(
                id=r.id,
                filename=r.filename,
                filepath=r.filepath,
                created_at=r.created_at,
            )
            for r in records
        ],
    )
