from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import uuid
import os
from io import BytesIO

from models.sql.audio_asset import AudioAsset
from services.database import get_async_session
from middlewares.auth_middleware import require_auth

AUDIO_ROUTER = APIRouter(prefix="/audio", tags=["Audio"])


def get_audio_url(audio_id: uuid.UUID) -> str:
    """Generate URL for accessing audio from database"""
    return f"/api/v1/ppt/audio/{audio_id}/data"


@AUDIO_ROUTER.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(require_auth),
    sql_session: AsyncSession = Depends(get_async_session)
):
    """Upload an audio file and store in database"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Determine content type
        content_type = file.content_type or "audio/wav"
        
        # Create audio asset with binary data
        audio_asset = AudioAsset(
            binary_data=file_content,
            filename=file.filename,
            content_type=content_type,
            file_size=len(file_content),
            is_uploaded=True,
            user_id=user_id
        )

        sql_session.add(audio_asset)
        await sql_session.commit()
        
        # Return with URL for fetching
        audio_asset.path = get_audio_url(audio_asset.id)
        audio_asset.binary_data = None  # Don't send binary in response

        return audio_asset
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload audio: {str(e)}")


@AUDIO_ROUTER.get("/uploaded", response_model=List[AudioAsset])
async def get_uploaded_audio(sql_session: AsyncSession = Depends(get_async_session)):
    """Get list of uploaded audio files"""
    try:
        audios = await sql_session.scalars(
            select(AudioAsset)
            .where(AudioAsset.is_uploaded == True)
            .order_by(AudioAsset.created_at.desc())
        )
        audios_list = audios.all()
        # Replace path with URL to fetch binary data
        for audio in audios_list:
            audio.path = get_audio_url(audio.id)
            # Don't send binary data in list responses
            audio.binary_data = None
        return audios_list
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve uploaded audio: {str(e)}"
        )


@AUDIO_ROUTER.get("/generated", response_model=List[AudioAsset])
async def get_generated_audio(sql_session: AsyncSession = Depends(get_async_session)):
    """Get list of generated audio files (TTS, etc.)"""
    try:
        audios = await sql_session.scalars(
            select(AudioAsset)
            .where(AudioAsset.is_uploaded == False)
            .order_by(AudioAsset.created_at.desc())
        )
        audios_list = audios.all()
        # Replace path with URL to fetch binary data
        for audio in audios_list:
            audio.path = get_audio_url(audio.id)
            # Don't send binary data in list responses
            audio.binary_data = None
        return audios_list
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve generated audio: {str(e)}"
        )


@AUDIO_ROUTER.delete("/{id}", status_code=204)
async def delete_audio_by_id(
    id: uuid.UUID, sql_session: AsyncSession = Depends(get_async_session)
):
    """Delete an audio file"""
    try:
        audio = await sql_session.get(AudioAsset, id)
        if not audio:
            raise HTTPException(status_code=404, detail="Audio not found")

        # Remove local file if it exists (for backward compatibility)
        if audio.path and os.path.exists(audio.path):
            try:
                os.remove(audio.path)
            except Exception as e:
                print(f"Warning: Could not remove file {audio.path}: {e}")

        await sql_session.delete(audio)
        await sql_session.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete audio: {str(e)}")


@AUDIO_ROUTER.get("/{id}/data")
async def get_audio_data(
    id: uuid.UUID, sql_session: AsyncSession = Depends(get_async_session)
):
    """Serve audio binary data from database"""
    try:
        audio = await sql_session.get(AudioAsset, id)
        if not audio:
            raise HTTPException(status_code=404, detail="Audio not found")
        
        if not audio.binary_data:
            # Fallback to file if binary data not available (backward compatibility)
            if audio.path and os.path.exists(audio.path):
                with open(audio.path, "rb") as f:
                    binary_data = f.read()
                content_type = audio.content_type or "audio/wav"
                return StreamingResponse(
                    BytesIO(binary_data),
                    media_type=content_type,
                    headers={
                        "Content-Length": str(len(binary_data))
                    }
                )
            raise HTTPException(status_code=404, detail="Audio data not found")
        
        content_type = audio.content_type or "audio/wav"
        return StreamingResponse(
            BytesIO(audio.binary_data),
            media_type=content_type,
            headers={
                "Content-Length": str(len(audio.binary_data))
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audio: {str(e)}")
