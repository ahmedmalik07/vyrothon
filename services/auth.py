"""
auth.py — Selfie authentication service.

Takes an uploaded image, extracts the face embedding,
and matches it against all known grab_ids in the database.
"""

import numpy as np
import cv2
from sqlalchemy.orm import Session

from models import Face
from services.face_engine import extract_faces_from_array, find_match


def authenticate_selfie(image_bytes: bytes, db: Session) -> dict:
    """
    Authenticate a user via selfie image.

    Args:
        image_bytes: Raw bytes of the uploaded image file.
        db: Database session.

    Returns:
        Dict with grab_id, confidence, authenticated on success.

    Raises:
        ValueError: If no face detected in image.
        LookupError: If no matching identity found.
    """
    # Decode image bytes to numpy array
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image file. Ensure it is a valid image.")

    # Convert BGR roughly to YUV to equalize the Y channel (luminance)
    # This solves the exact "backlighting" issue seen on the webcam!
    img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) 
    # Much better than global equalizeHist for faces
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0])
    
    # Convert back to RGB for face_recognition
    img_rgb = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2RGB)

    # Extract face embeddings
    encodings = extract_faces_from_array(img_rgb)
    if not encodings:
        # Fallback to pure RGB if CLAHE messed up the gradient
        img_rgb_native = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = extract_faces_from_array(img_rgb_native)
        
    if not encodings:
        raise ValueError("No face detected in the uploaded image. Please ensure sufficient lighting.")

    # Load all known faces
    all_faces = db.query(Face).all()
    face_cache = [
        {"grab_id": str(f.grab_id), "embedding": np.array(f.embedding)}
        for f in all_faces
    ]

    if not face_cache:
        raise LookupError("No faces have been indexed yet. Run /ingest first.")

    # Match the first (largest) face in the selfie
    grab_id, confidence = find_match(encodings[0], face_cache)

    if grab_id is None:
        raise LookupError("No matching identity found in the database.")

    return {
        "grab_id": grab_id,
        "confidence": confidence,
        "authenticated": True,
    }
