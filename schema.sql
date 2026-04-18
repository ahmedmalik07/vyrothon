-- ============================================================
-- Wyibe Database Schema
-- Intelligent Identity & Retrieval Engine
-- ============================================================

-- Enable pgvector extension for 128-d face embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- Table: faces
-- Stores unique face embeddings with a grab_id (person identifier)
-- ============================================================
CREATE TABLE IF NOT EXISTS faces (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grab_id     UUID NOT NULL,
    embedding   vector(128) NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index on grab_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_faces_grab_id ON faces(grab_id);

-- ============================================================
-- Table: images
-- Stores metadata about ingested images
-- ============================================================
CREATE TABLE IF NOT EXISTS images (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename    TEXT NOT NULL,
    filepath    TEXT NOT NULL UNIQUE,   -- UNIQUE for idempotent ingest
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index on filepath for idempotent ingest checks
CREATE INDEX IF NOT EXISTS idx_images_filepath ON images(filepath);

-- ============================================================
-- Table: image_faces (many-to-many join)
-- Maps images to the faces (grab_ids) detected within them
-- One image can contain multiple faces (multi-face requirement)
-- One face/grab_id can appear in multiple images
-- ============================================================
CREATE TABLE IF NOT EXISTS image_faces (
    image_id    UUID NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    grab_id     UUID NOT NULL,
    PRIMARY KEY (image_id, grab_id)
);

-- Index for reverse lookup: all images for a given grab_id
CREATE INDEX IF NOT EXISTS idx_image_faces_grab_id ON image_faces(grab_id);
