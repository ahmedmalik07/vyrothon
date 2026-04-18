"""
face_engine.py — Pure face recognition utility (no FastAPI dependency).

Provides:
  - extract_faces(): Detect and encode all faces in an image → list of 128-d embeddings
  - find_match():    Compare an embedding against known faces → best grab_id or None

Uses dlib-backed face_recognition lib for detection + encoding.
Designed to be unit-testable in isolation.
"""

import face_recognition
import numpy as np
from typing import Optional

# Similarity threshold for face matching.
# face_recognition uses Euclidean distance on 128-d embeddings.
# Lower = stricter matching. 0.55 is the balanced sweet spot.
SIMILARITY_THRESHOLD = 0.55


def extract_faces(image_path: str) -> list[np.ndarray]:
    """
    Detect all faces in an image and return their 128-d embeddings.

    Args:
        image_path: Filesystem path to the image file.

    Returns:
        List of numpy arrays, each of shape (128,). One per detected face.
        Returns empty list if no faces found or image cannot be loaded.
    """
    try:
        img = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(img)
        return encodings
    except Exception:
        # Bad image file, corrupted, etc. — skip gracefully.
        return []


def extract_faces_from_array(img_rgb: np.ndarray) -> list[np.ndarray]:
    """
    Extract face embeddings from an in-memory RGB numpy array.
    Used for selfie auth where image comes from upload. Handles bad webcam lighting.
    """
    try:
        # First pass: Default fast detection
        locations = face_recognition.face_locations(img_rgb, model="hog")
        if not locations:
            # Second pass: Slower but more robust detection (upsample image to find smaller/darker faces)
            locations = face_recognition.face_locations(img_rgb, number_of_times_to_upsample=2, model="hog")
            
        if not locations:
            return []

        # Jitters=2 applies random perturbations to help with poor camera angles
        encodings = face_recognition.face_encodings(img_rgb, known_face_locations=locations, num_jitters=2)
        return encodings
    except Exception:
        return []


def find_match(
    embedding: np.ndarray,
    known_faces: list[dict],
    threshold: float = SIMILARITY_THRESHOLD,
) -> tuple[Optional[str], float]:
    """
    Compare a face embedding against all known faces.

    Args:
        embedding:   128-d numpy array of the query face.
        known_faces: List of dicts with keys 'grab_id' (str/UUID) and 'embedding' (np.ndarray).
        threshold:   Maximum distance to consider a match (lower = stricter).

    Returns:
        Tuple of (grab_id, confidence) if match found, else (None, 0.0).
        confidence = 1.0 - distance (higher is better).
    """
    if not known_faces:
        return None, 0.0

    known_embeddings = [f["embedding"] for f in known_faces]
    distances = face_recognition.face_distance(known_embeddings, embedding)

    best_idx = int(np.argmin(distances))
    best_distance = float(distances[best_idx])

    if best_distance < threshold:
        grab_id = known_faces[best_idx]["grab_id"]
        confidence = round(1.0 - best_distance, 4)
        return str(grab_id), confidence

    return None, 0.0
