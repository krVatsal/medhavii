-- Migration: Add User table and link media to users
-- Database: PostgreSQL
-- Date: 2026-01-02

-- ============================================================================
-- USER TABLE CREATION
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

-- Add indexes for user table
CREATE INDEX IF NOT EXISTS idx_user_google_id ON "user"(google_id);
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_user_is_active ON "user"(is_active);

-- ============================================================================
-- ADD USER_ID TO MEDIA TABLES
-- ============================================================================

-- Add user_id to imageasset
ALTER TABLE imageasset 
  ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES "user"(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_imageasset_user_id ON imageasset(user_id);

-- Add user_id to videoasset
ALTER TABLE videoasset 
  ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES "user"(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_videoasset_user_id ON videoasset(user_id);

-- Add user_id to audioasset
ALTER TABLE audioasset 
  ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES "user"(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_audioasset_user_id ON audioasset(user_id);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE "user" IS 'Users authenticated via Google OAuth';
COMMENT ON COLUMN "user".google_id IS 'Google OAuth subject identifier';
COMMENT ON COLUMN "user".email IS 'User email from Google account';
COMMENT ON COLUMN "user".picture IS 'URL to user profile picture from Google';
COMMENT ON COLUMN "user".last_login IS 'Last successful login timestamp';

COMMENT ON COLUMN imageasset.user_id IS 'Owner of the image asset';
COMMENT ON COLUMN videoasset.user_id IS 'Owner of the video asset';
COMMENT ON COLUMN audioasset.user_id IS 'Owner of the audio asset';
