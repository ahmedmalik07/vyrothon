"""
test_api.py — Smoke tests for Wyibe API.

These tests use FastAPI's TestClient (no real DB needed for health check).
For ingest/auth tests, a running Postgres with pgvector is required.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Set a test DATABASE_URL before importing the app
# (In CI, override via environment variable)
os.environ.setdefault("DATABASE_URL", "sqlite:///./wyibe.db")

from main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Health check should always return 200 with status ok."""

    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_body(self):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"


class TestIngestEndpoint:
    """Ingest endpoint validation tests."""

    def test_ingest_invalid_folder_returns_400(self):
        """Posting a non-existent folder should return 400."""
        response = client.post("/ingest", json={"folder": "./nonexistent_folder_xyz"})
        assert response.status_code == 400

    def test_ingest_missing_folder_returns_422(self):
        """Missing required field should return 422 (Pydantic validation)."""
        response = client.post("/ingest", json={})
        assert response.status_code == 422

    def test_ingest_empty_folder_returns_200(self):
        """Ingesting an empty folder should succeed with zero counts."""
        # Create a temp empty folder
        empty_dir = os.path.join(os.path.dirname(__file__), "_test_empty_dir")
        os.makedirs(empty_dir, exist_ok=True)
        try:
            response = client.post("/ingest", json={"folder": empty_dir})
            assert response.status_code == 200
            data = response.json()
            assert data["indexed_images"] == 0
            assert data["total_faces"] == 0
        finally:
            os.rmdir(empty_dir)


class TestSelfieAuthEndpoint:
    """Selfie auth endpoint validation tests."""

    def test_selfie_no_file_returns_422(self):
        """Missing file should return 422."""
        response = client.post("/auth/selfie")
        assert response.status_code == 422

    def test_selfie_blank_image_returns_422(self):
        """A blank/invalid image should return 422 (no face detected)."""
        # Create a minimal 1x1 PNG (no face)
        import io
        from PIL import Image as PILImage

        img = PILImage.new("RGB", (10, 10), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        response = client.post(
            "/auth/selfie",
            files={"file": ("blank.png", buf, "image/png")},
        )
        assert response.status_code == 422


class TestImagesEndpoint:
    """Image retrieval endpoint tests."""

    def test_images_invalid_grab_id_returns_404(self):
        """A random UUID should return 404 (no images)."""
        import uuid
        fake_id = str(uuid.uuid4())
        response = client.get(f"/images/{fake_id}")
        assert response.status_code == 404

    def test_images_invalid_uuid_format_returns_422(self):
        """A non-UUID string should return 422."""
        response = client.get("/images/not-a-uuid")
        assert response.status_code == 422


class TestFacesEndpoint:
    """Faces listing endpoint tests."""

    def test_faces_returns_200(self):
        response = client.get("/faces")
        assert response.status_code == 200
        data = response.json()
        assert "total_identities" in data
        assert "faces" in data
