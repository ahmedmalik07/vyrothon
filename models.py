"""
models.py — SQLAlchemy ORM models for Wyibe.

Tables:
  - faces:       Stores unique face embeddings with a grab_id (person identifier)
  - images:      Stores metadata about ingested images
  - image_faces: Many-to-many join table (one image → many faces, one face → many images)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, JSON, UUID
from sqlalchemy.orm import relationship
# from pgvector.sqlalchemy import Vector

from database import Base


class Face(Base):
    """A unique face embedding linked to a grab_id (person identifier)."""
    __tablename__ = "faces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grab_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    embedding = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Face grab_id={self.grab_id}>"


class Image(Base):
    """Metadata for an ingested image file."""
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False, unique=True)  # unique for idempotent ingest
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship to grab_ids via join table
    face_links = relationship("ImageFace", back_populates="image", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Image filename={self.filename}>"


class ImageFace(Base):
    """Many-to-many join: maps images to the faces (grab_ids) detected within them."""
    __tablename__ = "image_faces"

    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), primary_key=True)
    grab_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True, index=True)

    image = relationship("Image", back_populates="face_links")

    def __repr__(self):
        return f"<ImageFace image_id={self.image_id} grab_id={self.grab_id}>"
