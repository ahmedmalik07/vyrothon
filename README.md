# Wyibe

![Architecture Engine](https://img.shields.io/badge/Architecture-Spec_Driven-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)

Wyibe is a high-performance image processing backend designed for large-scale events. It uses facial recognition to automatically group images by identity and provides a secure **"Selfie-as-a-Key"** retrieval system.

> Imagine a marathon with 500 runners and photographers taking 50,000 photos. Instead of manual tagging, Wyibe automatically detects faces, assigns unique identifiers, and lets each runner retrieve their photos with a single selfie.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                          │
│  Local Folder ──→ Crawler (os.walk + glob)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ crawl
┌──────────────────────────▼──────────────────────────────────┐
│                     PIPELINE LAYER                          │
│  Face Detection ──→ Grab ID Assign ──→ PostgreSQL + pgvector│
│  (face_recognition)  (cosine sim)      (faces, images,      │
│  → 128-d vectors                        image_faces)        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                       API LAYER                             │
│  FastAPI · auto-Swagger · Pydantic validation               │
│                                                             │
│  POST /ingest      POST /auth/selfie    GET /images/{id}    │
│  (25% weight)      (15% weight)         (retrieval)         │
│                                                             │
│  GET /health       GET /faces           GET /docs           │
│                    (bonus)              (Swagger UI)         │
│                                                             │
│  Global error handler · Pydantic schemas · HTTP codes       │
└──────────────────────────┴──────────────────────────────────┘
```

---

## Database Schema (ERD)

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│      faces       │       │   image_faces    │       │     images       │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id       UUID PK │       │ image_id UUID FK─┼──────→│ id       UUID PK │
│ grab_id  UUID    │←──────┼─grab_id  UUID FK │       │ filename TEXT    │
│ embedding vec128 │       │ (composite PK)   │       │ filepath TEXT UQ │
│ created_at TSTZ  │       └──────────────────┘       │ created_at TSTZ  │
└──────────────────┘                                  └──────────────────┘
        1:N                        M:N                        1:N
   (one grab_id,              (one image →               (one image,
    many embeddings)           many faces)                 unique path)
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI (Python) |
| Database | PostgreSQL + pgvector |
| ORM | SQLAlchemy |
| Face Recognition | face_recognition (dlib) |
| Image Processing | OpenCV, Pillow |
| Validation | Pydantic v2 |
| Docs | Swagger UI (auto-generated) |

---

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ with pgvector extension
- CMake + dlib (for face_recognition)

### Installation

```bash
# 1. Clone the repository
git clone <repository_url>
cd wyibe

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup PostgreSQL
psql -U postgres -c "CREATE DATABASE wyibe;"
psql -U postgres -d wyibe -c "CREATE EXTENSION IF NOT EXISTS vector;"

Copy the `.env.example` file to `.env` and fill it out:
```bash
# Default: postgresql://postgres:postgres@localhost:5432/wyibe
DATABASE_URL=postgresql://user:password@host:port/dbnameain:app --reload --host 0.0.0.0 --port 8000
```

### Swagger UI
Navigate to **http://localhost:8000/docs** for interactive API documentation.

---

## API Reference

### `GET /health` — Health Check
```bash
curl http://localhost:8000/health
```
**Response:**
```json
{ "status": "ok" }
```

---

### `POST /ingest` — Ingest Images from Folder
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"folder": "./sample_images"}'
```
**Response:**
```json
{
  "indexed_images": 150,
  "total_faces": 237,
  "skipped_images": 12
}
```

---

### `POST /auth/selfie` — Authenticate via Selfie
```bash
curl -X POST http://localhost:8000/auth/selfie \
  -F "file=@/path/to/selfie.jpg"
```
**Response (200):**
```json
{
  "grab_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "confidence": 0.8234,
  "authenticated": true
}
```
**Response (422 — no face):**
```json
{ "detail": "No face detected in the uploaded image." }
```

---

### `GET /images/{grab_id}` — Retrieve Images by Identity
```bash
curl http://localhost:8000/images/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```
**Response:**
```json
{
  "grab_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "total_images": 5,
  "images": [
    {
      "filename": "IMG_0042.jpg",
      "filepath": "/photos/marathon/IMG_0042.jpg",
      "created_at": "2026-04-18T10:30:00Z"
    }
  ]
}
```

---

### `GET /faces` — List All Known Identities (Bonus)
```bash
curl http://localhost:8000/faces
```
**Response:**
```json
{
  "total_identities": 42,
  "faces": [
    { "grab_id": "a1b2c3d4-...", "image_count": 7 },
    { "grab_id": "f9e8d7c6-...", "image_count": 3 }
  ]
}
```

---

## Running Tests

```bash
pytest test_api.py -v
```

---

## Error Handling

All endpoints return consistent JSON error responses:

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 400 | Bad request (e.g., invalid folder path) |
| 404 | Not found (e.g., no images for grab_id) |
| 422 | Unprocessable entity (e.g., no face in image) |
| 500 | Internal server error (global handler) |

---

## Key Design Decisions

1. **Idempotent Ingest**: `filepath` is UNIQUE — re-running ingest on the same folder skips already-indexed images.
2. **Confidence Score**: Selfie auth returns `1 - euclidean_distance` as a confidence float.
3. **Multi-face Support**: One image can contain multiple people; `image_faces` is a many-to-many join table.
4. **Face Cache**: All known embeddings are loaded once per request, not per-image, for performance.
5. **Pure Service Layer**: `face_engine.py` has zero FastAPI dependency — fully unit-testable.

---

## Project Structure

```
wyibe/
├── database.py       <-- Database connection & Base
├── main.py           <-- FastAPI application instancer mounts + global error handler
├── models.py            ← SQLAlchemy ORM models (faces, images, image_faces)
├── schemas.py           ← Pydantic request/response schemas
├── database.py          ← Engine, SessionLocal, Base, init_db
├── schema.sql           ← Raw SQL schema definition (spec-first)
├── services/
│   ├── face_engine.py   ← Face detection + embedding + matching (pure utility)
│   ├── ingest.py        ← Folder crawl + face indexing logic
│   └── auth.py          ← Selfie authentication logic
├── routers/
│   ├── ingest.py        ← POST /ingest
│   ├── auth.py          ← POST /auth/selfie
│   └── images.py        ← GET /images/{grab_id}
├── test_api.py          ← Smoke tests (pytest)
├── requirements.txt     ← Dependencies
├── .env                 ← DATABASE_URL config
└── README.md            ← This file
```
