"""
schemas.py — Pydantic request/response schemas for Wyibe API.

Every endpoint uses a typed response_model for consistent API output.
This gives us automatic validation + Swagger docs for free.
"""

from datetime import datetime
from uuid import UUID
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
# Health
# ============================================================
class HealthResponse(BaseModel):
    status: str = "ok"


# ============================================================
# Ingest
# ============================================================
class IngestRequest(BaseModel):
    folder: str = Field(..., description="Path to folder containing images to ingest", examples=["./sample_images"])


class IngestResponse(BaseModel):
    indexed_images: int = Field(..., description="Number of images successfully indexed")
    total_faces: int = Field(..., description="Total number of face detections across all images")
    skipped_images: int = Field(0, description="Images skipped (already ingested or no faces)")


# ============================================================
# Selfie Auth
# ============================================================
class AuthResponse(BaseModel):
    grab_id: str = Field(..., description="The unique identity identifier for the matched face")
    confidence: float = Field(..., description="Match confidence score (0.0 to 1.0, higher is better)")
    authenticated: bool = Field(True, description="Whether the selfie was successfully authenticated")


# ============================================================
# Image Retrieval
# ============================================================
class ImageInfo(BaseModel):
    id: UUID
    filename: str
    filepath: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ImagesResponse(BaseModel):
    grab_id: str
    total_images: int
    images: List[ImageInfo]


# ============================================================
# Faces listing (bonus differentiator)
# ============================================================
class FaceInfo(BaseModel):
    grab_id: str
    image_count: int


class FacesListResponse(BaseModel):
    total_identities: int
    faces: List[FaceInfo]


# ============================================================
# Error
# ============================================================
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    path: Optional[str] = None
