# Media Storage Migration Guide

This guide explains how to migrate from filesystem-based media storage to database-based storage for images, videos, and audio files.

## Overview

The system now stores media files (images, videos, audio) directly in the database as binary data (`BLOB`/`BYTEA`) instead of saving them to the filesystem. This provides several benefits:

- **Simplified deployment**: No need to manage separate file storage
- **Better consistency**: Database ACID properties ensure data integrity
- **Easier backups**: Single database backup includes all media
- **Scalability**: Easier to scale horizontally with managed databases

## Database Changes

### New Fields Added to Existing Tables

#### `imageasset` table:
- `binary_data` (BYTEA/BLOB): Stores the actual image binary data
- `filename` (VARCHAR): Original filename
- `content_type` (VARCHAR): MIME type (e.g., "image/png", "image/jpeg")
- `file_size` (INTEGER): Size in bytes
- `path` is now OPTIONAL for backward compatibility

#### `videoasset` table:
- `binary_data` (BYTEA/BLOB): Stores the actual video binary data
- `filename` (VARCHAR): Original filename
- `content_type` (VARCHAR): MIME type (e.g., "video/mp4")
- `file_size` (INTEGER): Size in bytes
- `path` is now OPTIONAL for backward compatibility

#### New `audioasset` table:
- `id` (UUID): Primary key
- `created_at` (TIMESTAMP WITH TIMEZONE): Creation timestamp
- `is_uploaded` (BOOLEAN): Whether user-uploaded or generated
- `path` (VARCHAR, OPTIONAL): Deprecated, for backward compatibility
- `binary_data` (BYTEA/BLOB): The actual audio binary data
- `filename` (VARCHAR): Original filename
- `content_type` (VARCHAR): MIME type (e.g., "audio/wav", "audio/mp3")
- `file_size` (INTEGER): Size in bytes
- `language_code` (VARCHAR): For TTS audio (e.g., "en", "hi")
- `extras` (JSON): Additional metadata

## SQL Migration Scripts

### PostgreSQL:

```sql
-- Add new columns to imageasset
ALTER TABLE imageasset 
  ADD COLUMN binary_data BYTEA,
  ADD COLUMN filename VARCHAR(255),
  ADD COLUMN content_type VARCHAR(100) DEFAULT 'image/png',
  ADD COLUMN file_size INTEGER,
  ALTER COLUMN path DROP NOT NULL;

-- Add new columns to videoasset
ALTER TABLE videoasset 
  ADD COLUMN binary_data BYTEA,
  ADD COLUMN filename VARCHAR(255),
  ADD COLUMN content_type VARCHAR(100) DEFAULT 'video/mp4',
  ADD COLUMN file_size INTEGER,
  ALTER COLUMN path DROP NOT NULL;

-- Create audioasset table
CREATE TABLE audioasset (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_uploaded BOOLEAN NOT NULL DEFAULT FALSE,
    path VARCHAR(500),
    binary_data BYTEA,
    filename VARCHAR(255),
    content_type VARCHAR(100) DEFAULT 'audio/wav',
    file_size INTEGER,
    language_code VARCHAR(10),
    extras JSON
);

CREATE INDEX idx_audioasset_created_at ON audioasset(created_at DESC);
CREATE INDEX idx_audioasset_is_uploaded ON audioasset(is_uploaded);
CREATE INDEX idx_audioasset_language_code ON audioasset(language_code);
```

### SQLite:

```sql
-- Add new columns to imageasset
ALTER TABLE imageasset ADD COLUMN binary_data BLOB;
ALTER TABLE imageasset ADD COLUMN filename TEXT;
ALTER TABLE imageasset ADD COLUMN content_type TEXT DEFAULT 'image/png';
ALTER TABLE imageasset ADD COLUMN file_size INTEGER;

-- Add new columns to videoasset
ALTER TABLE videoasset ADD COLUMN binary_data BLOB;
ALTER TABLE videoasset ADD COLUMN filename TEXT;
ALTER TABLE videoasset ADD COLUMN content_type TEXT DEFAULT 'video/mp4';
ALTER TABLE videoasset ADD COLUMN file_size INTEGER;

-- Create audioasset table
CREATE TABLE audioasset (
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

CREATE INDEX idx_audioasset_created_at ON audioasset(created_at DESC);
CREATE INDEX idx_audioasset_is_uploaded ON audioasset(is_uploaded);
```

## API Changes

### New Endpoints

#### Images:
- `GET /api/v1/ppt/images/{id}/data` - Retrieve image binary data
- Existing endpoints now return URLs pointing to `/api/v1/ppt/images/{id}/data`

#### Videos:
- `POST /api/v1/ppt/videos/upload` - Upload video
- `GET /api/v1/ppt/videos/{id}/data` - Retrieve video binary data
- `GET /api/v1/ppt/videos/uploaded` - List uploaded videos
- `GET /api/v1/ppt/videos/generated` - List generated videos
- `DELETE /api/v1/ppt/videos/{id}` - Delete video

#### Audio:
- `POST /api/v1/ppt/audio/upload` - Upload audio
- `GET /api/v1/ppt/audio/{id}/data` - Retrieve audio binary data
- `GET /api/v1/ppt/audio/uploaded` - List uploaded audio
- `GET /api/v1/ppt/audio/generated` - List generated audio
- `DELETE /api/v1/ppt/audio/{id}` - Delete audio

### Modified Behavior

1. **Image Upload/Generation**: Now stores binary data in database instead of saving to `app_data/images/`
2. **Video Generation**: Manim videos stored in database instead of `app_data/videos/`
3. **Audio Generation**: TTS audio stored in database instead of `app_data/exports/narrations/`

## Migration Steps

### 1. Backup Your Data

```bash
# Backup database
pg_dump your_database > backup.sql

# Backup media files (in case you need to rollback)
tar -czf media_backup.tar.gz /path/to/app_data
```

### 2. Run Database Migration

```bash
# For PostgreSQL
psql your_database < migration.sql

# For SQLite
sqlite3 your_database.db < migration_sqlite.sql
```

### 3. Migrate Existing Files to Database (Optional)

If you have existing files in the filesystem that you want to migrate to the database, run this script:

```python
# migrate_files_to_db.py
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import select
from models.sql.image_asset import ImageAsset
from models.sql.video_asset import VideoAsset
from utils.get_env import get_app_data_directory_env

async def migrate_files():
    engine = create_async_engine("your_database_url")
    
    async with AsyncSession(engine) as session:
        # Migrate images
        images = await session.scalars(select(ImageAsset))
        for image in images.all():
            if image.path and os.path.exists(image.path) and not image.binary_data:
                with open(image.path, "rb") as f:
                    image.binary_data = f.read()
                    image.file_size = len(image.binary_data)
                    image.filename = os.path.basename(image.path)
                print(f"Migrated image: {image.id}")
        
        # Migrate videos
        videos = await session.scalars(select(VideoAsset))
        for video in videos.all():
            if video.path and os.path.exists(video.path) and not video.binary_data:
                with open(video.path, "rb") as f:
                    video.binary_data = f.read()
                    video.file_size = len(video.binary_data)
                    video.filename = os.path.basename(video.path)
                print(f"Migrated video: {video.id}")
        
        await session.commit()

if __name__ == "__main__":
    asyncio.run(migrate_files())
```

### 4. Update Application Code

The following services have been updated:
- ✅ `api/v1/ppt/endpoints/images.py` - Image endpoints
- ✅ `api/v1/ppt/endpoints/videos.py` - Video endpoints (NEW)
- ✅ `api/v1/ppt/endpoints/audio.py` - Audio endpoints (NEW)
- ✅ `models/sql/image_asset.py` - Image model
- ✅ `models/sql/video_asset.py` - Video model
- ✅ `models/sql/audio_asset.py` - Audio model (NEW)
- ⚠️  `services/image_generation_service.py` - Needs update
- ⚠️  `services/manim_service.py` - Needs update
- ⚠️  `services/bhashini_tts_service.py` - Needs update
- ⚠️  `services/gemini_tts_service.py` - Needs update
- ⚠️  `services/pptx_presentation_creator.py` - Needs update to fetch from DB

### 5. Test the Migration

```bash
# Start the application
python -m uvicorn server:app --reload

# Test image upload
curl -X POST http://localhost:8000/api/v1/ppt/images/upload \
  -F "file=@test.png"

# Test image retrieval
curl http://localhost:8000/api/v1/ppt/images/{id}/data > downloaded.png
```

### 6. Clean Up (Optional)

After verifying everything works, you can remove the old media files:

```bash
# Remove old files (BE CAREFUL!)
rm -rf /path/to/app_data/images/*
rm -rf /path/to/app_data/videos/*
rm -rf /path/to/app_data/exports/narrations/*
```

## Rollback Plan

If you need to rollback:

1. Restore database from backup:
   ```bash
   psql your_database < backup.sql
   ```

2. Restore media files:
   ```bash
   tar -xzf media_backup.tar.gz -C /
   ```

3. Revert code changes:
   ```bash
   git checkout HEAD~1
   ```

## Performance Considerations

### Database Size
- Images: ~100KB - 2MB each
- Videos: ~1MB - 100MB each
- Audio: ~50KB - 5MB each

### Recommendations
1. Use PostgreSQL instead of SQLite for production
2. Consider setting up database connection pooling
3. Monitor database size and performance
4. For very large media files (>10MB), consider using cloud storage (S3, Azure Blob) with database storing URLs

### Optimization
- Enable database compression if available
- Use streaming responses for large files
- Implement caching layer (Redis) for frequently accessed media
- Consider CDN for serving media

## Backward Compatibility

The system maintains backward compatibility:
- Old records with only `path` field will still work
- Endpoints check for `binary_data` first, then fall back to reading from `path`
- This allows gradual migration of existing data

## Environment Variables

No new environment variables required. The following are still used for temporary file operations:
- `APP_DATA_DIRECTORY` - For temp files during generation
- `TEMP_DIRECTORY` - For temporary processing

## Support

If you encounter issues during migration:
1. Check database logs
2. Verify all migrations ran successfully
3. Ensure application has proper database permissions
4. Check disk space on database server
