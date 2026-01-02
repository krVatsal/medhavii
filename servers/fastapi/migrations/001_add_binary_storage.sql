-- Migration: Add binary storage columns to media tables
-- Database: PostgreSQL
-- Date: 2026-01-02

-- ============================================================================
-- IMAGE ASSET TABLE MODIFICATIONS
-- ============================================================================

-- Add new columns for binary storage
-- Check all tables exist

ALTER TABLE imageasset 
  ADD COLUMN IF NOT EXISTS binary_data BYTEA,
  ADD COLUMN IF NOT EXISTS filename VARCHAR(255),
  ADD COLUMN IF NOT EXISTS content_type VARCHAR(100) DEFAULT 'image/png',
  ADD COLUMN IF NOT EXISTS file_size INTEGER;

-- Make path column optional (for backward compatibility)
ALTER TABLE imageasset 
  ALTER COLUMN path DROP NOT NULL;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_imageasset_filename ON imageasset(filename);
CREATE INDEX IF NOT EXISTS idx_imageasset_content_type ON imageasset(content_type);

-- ============================================================================
-- VIDEO ASSET TABLE MODIFICATIONS
-- ============================================================================

-- Add new columns for binary storage
ALTER TABLE videoasset 
  ADD COLUMN IF NOT EXISTS binary_data BYTEA,
  ADD COLUMN IF NOT EXISTS filename VARCHAR(255),
  ADD COLUMN IF NOT EXISTS content_type VARCHAR(100) DEFAULT 'video/mp4',
  ADD COLUMN IF NOT EXISTS file_size INTEGER;

-- Make path column optional (for backward compatibility)
ALTER TABLE videoasset 
  ALTER COLUMN path DROP NOT NULL;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_videoasset_filename ON videoasset(filename);
CREATE INDEX IF NOT EXISTS idx_videoasset_content_type ON videoasset(content_type);

-- ============================================================================
-- AUDIO ASSET TABLE CREATION
-- ============================================================================

-- Create new audioasset table for TTS and uploaded audio files
CREATE TABLE IF NOT EXISTS audioasset (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_uploaded BOOLEAN NOT NULL DEFAULT FALSE,
    path VARCHAR(500),
    binary_data BYTEA,
    filename VARCHAR(255),
    content_type VARCHAR(100) DEFAULT 'audio/wav',
    file_size INTEGER,
    language_code VARCHAR(10),
    extras JSON
);

-- Add indexes for audio asset table
CREATE INDEX IF NOT EXISTS idx_audioasset_created_at ON audioasset(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audioasset_is_uploaded ON audioasset(is_uploaded);
CREATE INDEX IF NOT EXISTS idx_audioasset_language_code ON audioasset(language_code);
CREATE INDEX IF NOT EXISTS idx_audioasset_filename ON audioasset(filename);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN imageasset.binary_data IS 'Binary image data stored directly in database';
COMMENT ON COLUMN imageasset.filename IS 'Original filename of the image';
COMMENT ON COLUMN imageasset.content_type IS 'MIME type of the image (e.g., image/png, image/jpeg)';
COMMENT ON COLUMN imageasset.file_size IS 'Size of the image in bytes';

COMMENT ON COLUMN videoasset.binary_data IS 'Binary video data stored directly in database';
COMMENT ON COLUMN videoasset.filename IS 'Original filename of the video';
COMMENT ON COLUMN videoasset.content_type IS 'MIME type of the video (e.g., video/mp4)';
COMMENT ON COLUMN videoasset.file_size IS 'Size of the video in bytes';

COMMENT ON TABLE audioasset IS 'Audio assets including TTS generated audio and user uploads';
COMMENT ON COLUMN audioasset.binary_data IS 'Binary audio data stored directly in database';
COMMENT ON COLUMN audioasset.language_code IS 'Language code for TTS audio (e.g., en, hi, es)';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify table structures
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name IN ('imageasset', 'videoasset', 'audioasset')
-- ORDER BY table_name, ordinal_position;

-- Check for records with file data
-- SELECT 
--     'imageasset' as table_name,
--     COUNT(*) as total_records,
--     COUNT(binary_data) as with_binary_data,
--     COUNT(path) as with_path
-- FROM imageasset
-- UNION ALL
-- SELECT 
--     'videoasset' as table_name,
--     COUNT(*) as total_records,
--     COUNT(binary_data) as with_binary_data,
--     COUNT(path) as with_path
-- FROM videoasset
-- UNION ALL
-- SELECT 
--     'audioasset' as table_name,
--     COUNT(*) as total_records,
--     COUNT(binary_data) as with_binary_data,
--     COUNT(path) as with_path
-- FROM audioasset;
