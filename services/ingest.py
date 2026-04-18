"""
ingest.py — Service layer for crawling folders and indexing faces.

Core logic:
  1. Glob for image files recursively
  2. Skip already-ingested images (idempotent)
  3. Extract face embeddings from each image
  4. Match against existing faces or mint new grab_ids
  5. Persist everything in a single transaction
"""

import os
import uuid
from glob import glob

import numpy as np
from sqlalchemy.orm import Session

from models import Face, Image, ImageFace
from services.face_engine import extract_faces, find_match

# Supported image extensions
IMAGE_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp")


def crawl_images(folder: str) -> list[str]:
    """Recursively find all image files in a folder."""
    paths = []
    for ext in IMAGE_EXTENSIONS:
        paths.extend(glob(os.path.join(folder, "**", ext), recursive=True))
    return sorted(set(paths))  # deduplicate, sorted for determinism


def ingest_folder(folder: str, db: Session) -> dict:
    """
    Crawl a folder, extract faces, assign grab_ids, and persist everything.

    Returns stats dict: { indexed_images, total_faces, skipped_images }
    """
    image_paths = crawl_images(folder)

    stats = {"indexed_images": 0, "total_faces": 0, "skipped_images": 0}

    if not image_paths:
        return stats

    # Load all known faces into memory once (not per-image)
    all_faces = db.query(Face).all()
    face_cache = [
        {"grab_id": str(f.grab_id), "embedding": np.array(f.embedding)}
        for f in all_faces
    ]

    for path in image_paths:
        # Normalize path for consistent storage
        norm_path = os.path.normpath(os.path.abspath(path))

        # Idempotent: skip if already ingested
        existing = db.query(Image).filter(Image.filepath == norm_path).first()
        if existing:
            stats["skipped_images"] += 1
            continue

        # Extract face embeddings from image
        embeddings = extract_faces(norm_path)
        if not embeddings:
            stats["skipped_images"] += 1
            continue

        # Create image record
        img_record = Image(
            filename=os.path.basename(norm_path),
            filepath=norm_path,
        )
        db.add(img_record)
        db.flush()  # get img_record.id before creating join records

        # Process each face in the image (multi-face handling)
        for emb in embeddings:
            matched_grab_id, confidence = find_match(emb, face_cache)

            if matched_grab_id is None:
                # New face — mint a new grab_id
                matched_grab_id = str(uuid.uuid4())
                face = Face(
                    grab_id=uuid.UUID(matched_grab_id),
                    embedding=emb.tolist(),
                )
                db.add(face)
                face_cache.append({
                    "grab_id": matched_grab_id,
                    "embedding": emb,
                })

            # Link this face to this image
            db.add(ImageFace(
                image_id=img_record.id,
                grab_id=uuid.UUID(matched_grab_id),
            ))
            stats["total_faces"] += 1

        stats["indexed_images"] += 1

    db.commit()
    return stats
