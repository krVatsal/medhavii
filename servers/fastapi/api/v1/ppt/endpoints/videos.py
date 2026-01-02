from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import uuid
import os
from io import BytesIO

from models.sql.video_asset import VideoAsset
from services.database import get_async_session
from middlewares.auth_middleware import require_auth

VIDEOS_ROUTER = APIRouter(prefix="/videos", tags=["Videos"])


def get_video_url(video_id: uuid.UUID) -> str:
    """Generate URL for accessing video from database"""
    return f"/api/v1/ppt/videos/{video_id}/data"


@VIDEOS_ROUTER.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(require_auth),
    sql_session: AsyncSession = Depends(get_async_session)
):
    """Upload a video file and store in database"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Determine content type
        content_type = file.content_type or "video/mp4"
        
        # Create video asset with binary data
        video_asset = VideoAsset(
            binary_data=file_content,
            filename=file.filename,
            content_type=content_type,
            file_size=len(file_content),
            is_uploaded=True,
            user_id=user_id
        )

        sql_session.add(video_asset)
        await sql_session.commit()
        
        # Return with URL for fetching
        video_asset.path = get_video_url(video_asset.id)
        video_asset.binary_data = None  # Don't send binary in response

        return video_asset
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload video: {str(e)}")


@VIDEOS_ROUTER.get("/uploaded", response_model=List[VideoAsset])
async def get_uploaded_videos(sql_session: AsyncSession = Depends(get_async_session)):
    """Get list of uploaded videos"""
    try:
        videos = await sql_session.scalars(
            select(VideoAsset)
            .where(VideoAsset.is_uploaded == True)
            .order_by(VideoAsset.created_at.desc())
        )
        videos_list = videos.all()
        # Replace path with URL to fetch binary data
        for video in videos_list:
            video.path = get_video_url(video.id)
            # Don't send binary data in list responses
            video.binary_data = None
        return videos_list
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve uploaded videos: {str(e)}"
        )


@VIDEOS_ROUTER.get("/generated", response_model=List[VideoAsset])
async def get_generated_videos(sql_session: AsyncSession = Depends(get_async_session)):
    """Get list of generated videos"""
    try:
        videos = await sql_session.scalars(
            select(VideoAsset)
            .where(VideoAsset.is_uploaded == False)
            .order_by(VideoAsset.created_at.desc())
        )
        videos_list = videos.all()
        # Replace path with URL to fetch binary data
        for video in videos_list:
            video.path = get_video_url(video.id)
            # Don't send binary data in list responses
            video.binary_data = None
        return videos_list
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve generated videos: {str(e)}"
        )


@VIDEOS_ROUTER.delete("/{id}", status_code=204)
async def delete_video_by_id(
    id: uuid.UUID, sql_session: AsyncSession = Depends(get_async_session)
):
    """Delete a video"""
    try:
        video = await sql_session.get(VideoAsset, id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Remove local file if it exists (for backward compatibility)
        if video.path and os.path.exists(video.path):
            try:
                os.remove(video.path)
            except Exception as e:
                print(f"Warning: Could not remove file {video.path}: {e}")

        await sql_session.delete(video)
        await sql_session.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")


@VIDEOS_ROUTER.get("/{id}/data")
async def get_video_data(
    id: uuid.UUID, sql_session: AsyncSession = Depends(get_async_session)
):
    """Serve video binary data from database with streaming support"""
    try:
        video = await sql_session.get(VideoAsset, id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        if not video.binary_data:
            # Fallback to file if binary data not available (backward compatibility)
            if video.path and os.path.exists(video.path):
                with open(video.path, "rb") as f:
                    binary_data = f.read()
                content_type = video.content_type or "video/mp4"
                return StreamingResponse(
                    BytesIO(binary_data),
                    media_type=content_type,
                    headers={
                        "Accept-Ranges": "bytes",
                        "Content-Length": str(len(binary_data))
                    }
                )
            raise HTTPException(status_code=404, detail="Video data not found")
        
        content_type = video.content_type or "video/mp4"
        return StreamingResponse(
            BytesIO(video.binary_data),
            media_type=content_type,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(len(video.binary_data))
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve video: {str(e)}")
