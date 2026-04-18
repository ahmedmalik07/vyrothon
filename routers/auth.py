"""
routers/auth.py — POST /auth/selfie endpoint.

Weight: 15% of judging score.
Accepts an uploaded image file, matches the face against known identities,
returns grab_id + confidence score.
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas import AuthResponse, ErrorResponse
from services.auth import authenticate_selfie

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/selfie",
    response_model=AuthResponse,
    responses={
        404: {"model": ErrorResponse, "description": "No matching identity found"},
        422: {"model": ErrorResponse, "description": "No face detected in image"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Authenticate via selfie",
    description=(
        "Upload a selfie image. The system extracts the face embedding and compares it "
        "against all known identities. Returns the matching grab_id and a confidence score."
    ),
)
async def selfie_auth(
    file: UploadFile = File(..., description="Selfie image file (JPEG, PNG)"),
    db: Session = Depends(get_db),
):
    # Validate file type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid file type: '{file.content_type}'. Upload an image file.",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=422, detail="Empty file uploaded.")

    try:
        result = authenticate_selfie(contents, db)
    except ValueError as e:
        # No face detected or bad image
        raise HTTPException(status_code=422, detail=str(e))
    except LookupError as e:
        # No matching identity
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

    return AuthResponse(**result)
