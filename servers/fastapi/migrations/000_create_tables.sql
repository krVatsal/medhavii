-- Migration: Create all tables from scratch with binary storage and authentication
-- Database: PostgreSQL
-- Date: 2026-01-02

-- ============================================================================
-- USER TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS "user" (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    picture VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_user_google_id ON "user"(google_id);
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_user_is_active ON "user"(is_active);

-- ============================================================================
-- IMAGE ASSET TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS imageasset (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES "user"(id) ON DELETE CASCADE,
    is_uploaded BOOLEAN NOT NULL DEFAULT FALSE,
    path VARCHAR(500),
    binary_data BYTEA,
    filename VARCHAR(255),
    content_type VARCHAR(100) DEFAULT 'image/png',
    file_size INTEGER,
    extras JSON
);

CREATE INDEX IF NOT EXISTS idx_imageasset_created_at ON imageasset(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_imageasset_user_id ON imageasset(user_id);
CREATE INDEX IF NOT EXISTS idx_imageasset_is_uploaded ON imageasset(is_uploaded);

-- ============================================================================
-- VIDEO ASSET TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS videoasset (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES "user"(id) ON DELETE CASCADE,
    is_uploaded BOOLEAN NOT NULL DEFAULT FALSE,
    path VARCHAR(500),
    binary_data BYTEA,
    filename VARCHAR(255),
    content_type VARCHAR(100) DEFAULT 'video/mp4',
    file_size INTEGER,
    extras JSON
);

CREATE INDEX IF NOT EXISTS idx_videoasset_created_at ON videoasset(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_videoasset_user_id ON videoasset(user_id);
CREATE INDEX IF NOT EXISTS idx_videoasset_is_uploaded ON videoasset(is_uploaded);

-- ============================================================================
-- AUDIO ASSET TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS audioasset (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES "user"(id) ON DELETE CASCADE,
    is_uploaded BOOLEAN NOT NULL DEFAULT FALSE,
    path VARCHAR(500),
    binary_data BYTEA,
    filename VARCHAR(255),
    content_type VARCHAR(100) DEFAULT 'audio/wav',
    file_size INTEGER,
    language_code VARCHAR(10),
    extras JSON
);

CREATE INDEX IF NOT EXISTS idx_audioasset_created_at ON audioasset(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audioasset_user_id ON audioasset(user_id);
CREATE INDEX IF NOT EXISTS idx_audioasset_is_uploaded ON audioasset(is_uploaded);
CREATE INDEX IF NOT EXISTS idx_audioasset_language_code ON audioasset(language_code);

-- ============================================================================
-- VIDEO JOB TABLE (if needed)
-- ============================================================================

CREATE TABLE IF NOT EXISTS videojob (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    video_asset_id UUID REFERENCES videoasset(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    prompt TEXT,
    error_message TEXT,
    extras JSON
);

CREATE INDEX IF NOT EXISTS idx_videojob_video_asset_id ON videojob(video_asset_id);
CREATE INDEX IF NOT EXISTS idx_videojob_status ON videojob(status);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE "user" IS 'Users authenticated via Google OAuth';
COMMENT ON TABLE imageasset IS 'Image assets stored in database';
COMMENT ON TABLE videoasset IS 'Video assets stored in database';
COMMENT ON TABLE audioasset IS 'Audio assets including TTS and uploads';
COMMENT ON TABLE videojob IS 'Video generation job tracking';

-- Verification
SELECT 'Tables created successfully!' as message;
