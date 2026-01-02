-- Migration: Add binary storage columns to media tables
-- Database: SQLite
-- Date: 2026-01-02

-- ============================================================================
-- IMAGE ASSET TABLE MODIFICATIONS
-- ============================================================================

-- Add new columns for binary storage
ALTER TABLE imageasset ADD COLUMN binary_data BLOB;
ALTER TABLE imageasset ADD COLUMN filename TEXT;
ALTER TABLE imageasset ADD COLUMN content_type TEXT DEFAULT 'image/png';
ALTER TABLE imageasset ADD COLUMN file_size INTEGER;

-- Note: SQLite does not support dropping NOT NULL constraints
-- The path column will remain as-is for backward compatibility

-- ============================================================================
-- VIDEO ASSET TABLE MODIFICATIONS
-- ============================================================================

-- Add new columns for binary storage
ALTER TABLE videoasset ADD COLUMN binary_data BLOB;
ALTER TABLE videoasset ADD COLUMN filename TEXT;
ALTER TABLE videoasset ADD COLUMN content_type TEXT DEFAULT 'video/mp4';
ALTER TABLE videoasset ADD COLUMN file_size INTEGER;

-- ============================================================================
-- AUDIO ASSET TABLE CREATION
-- ============================================================================

-- Create new audioasset table for TTS and uploaded audio files
CREATE TABLE IF NOT EXISTS audioasset (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    is_uploaded INTEGER NOT NULL DEFAULT 0,
    path TEXT,
    binary_data BLOB,
    filename TEXT,
    content_type TEXT DEFAULT 'audio/wav',
    file_size INTEGER,
    language_code TEXT,
    extras TEXT
);

-- Add indexes for audio asset table
CREATE INDEX IF NOT EXISTS idx_audioasset_created_at ON audioasset(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audioasset_is_uploaded ON audioasset(is_uploaded);
CREATE INDEX IF NOT EXISTS idx_audioasset_language_code ON audioasset(language_code);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify table structures
-- PRAGMA table_info(imageasset);
-- PRAGMA table_info(videoasset);
-- PRAGMA table_info(audioasset);

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
