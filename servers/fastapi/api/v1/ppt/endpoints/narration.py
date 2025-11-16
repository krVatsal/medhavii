"""
API endpoints for voice narration feature
"""
import uuid
from typing import Annotated, List
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from models.voice_narration_models import (
    VoiceNarrationRequest,
    PresentationNarration,
    SlideNarration
)
from services.database import get_async_session
from services.teaching_script_generator import generate_teaching_scripts_for_presentation
from services.bhashini_tts_service import get_bhashini_service
from datetime import datetime


NARRATION_ROUTER = APIRouter(prefix="/narration", tags=["Voice Narration"])


@NARRATION_ROUTER.post("/generate", response_model=PresentationNarration)
async def generate_presentation_narration(
    request: Annotated[VoiceNarrationRequest, Body()],
    sql_session: AsyncSession = Depends(get_async_session),
):
    """
    Generate complete voice narration for a presentation
    
    This endpoint:
    1. Fetches all slides for the presentation
    2. Generates teaching-style scripts using LLM
    3. Converts scripts to speech using Bhashini API
    4. Returns narration data with audio URLs
    """
    
    # Fetch presentation
    presentation_id = uuid.UUID(request.presentation_id)
    presentation = await sql_session.get(PresentationModel, presentation_id)
    
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    # Fetch all slides ordered by index
    slides_result = await sql_session.execute(
        select(SlideModel)
        .where(SlideModel.presentation == presentation_id)
        .order_by(SlideModel.index)
    )
    slides = slides_result.scalars().all()
    
    if not slides:
        raise HTTPException(status_code=400, detail="No slides found in presentation")
    
    # Generate teaching scripts for all slides
    teaching_scripts = await generate_teaching_scripts_for_presentation(
        slides=slides,
        language=request.language_code,
        student_level=request.student_level,
        include_regional_references=request.include_regional_references,
        presentation_title=presentation.title
    )
    
    # Generate speech for each script
    bhashini_service = get_bhashini_service()
    slide_narrations: List[SlideNarration] = []
    total_duration = 0.0
    
    for script in teaching_scripts:
        try:
            # Generate speech using Bhashini
            file_path, audio_url = await bhashini_service.generate_speech(
                text=script.teaching_explanation,
                language_code=request.language_code,
                gender=request.voice_gender
            )
            
            slide_narration = SlideNarration(
                slide_index=script.slide_index,
                script=script.teaching_explanation,
                audio_url=audio_url,
                duration_seconds=script.estimated_duration_seconds,
                language=request.language_code
            )
            
            slide_narrations.append(slide_narration)
            total_duration += script.estimated_duration_seconds
            
        except Exception as e:
            print(f"Error generating narration for slide {script.slide_index}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate narration for slide {script.slide_index}: {str(e)}"
            )
    
    # Return complete narration data
    return PresentationNarration(
        presentation_id=str(presentation_id),
        slides=slide_narrations,
        total_duration_seconds=total_duration,
        language=request.language_code,
        created_at=datetime.now().isoformat()
    )


@NARRATION_ROUTER.post("/regenerate-slide")
async def regenerate_slide_narration(
    presentation_id: Annotated[str, Body()],
    slide_index: Annotated[int, Body()],
    language_code: Annotated[str, Body()] = "hi",
    voice_gender: Annotated[str, Body()] = "female",
    student_level: Annotated[str, Body()] = "intermediate",
    include_regional_references: Annotated[bool, Body()] = True,
    sql_session: AsyncSession = Depends(get_async_session),
) -> SlideNarration:
    """
    Regenerate narration for a single slide
    
    Useful when user wants to regenerate a specific slide's narration
    """
    
    # Fetch presentation
    pres_id = uuid.UUID(presentation_id)
    presentation = await sql_session.get(PresentationModel, pres_id)
    
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    # Fetch the specific slide
    slides_result = await sql_session.execute(
        select(SlideModel)
        .where(SlideModel.presentation == pres_id)
        .where(SlideModel.index == slide_index)
    )
    slide = slides_result.scalar_one_or_none()
    
    if not slide:
        raise HTTPException(status_code=404, detail=f"Slide {slide_index} not found")
    
    # Import the teaching script generator
    from services.teaching_script_generator import generate_teaching_script
    
    # Generate teaching script
    script = await generate_teaching_script(
        slide=slide,
        language=language_code,
        student_level=student_level,
        include_regional_references=include_regional_references,
        presentation_context=f"Presentation: {presentation.title}"
    )
    
    # Generate speech
    bhashini_service = get_bhashini_service()
    file_path, audio_url = await bhashini_service.generate_speech(
        text=script.teaching_explanation,
        language_code=language_code,
        gender=voice_gender
    )
    
    return SlideNarration(
        slide_index=slide_index,
        script=script.teaching_explanation,
        audio_url=audio_url,
        duration_seconds=script.estimated_duration_seconds,
        language=language_code
    )


@NARRATION_ROUTER.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages for voice narration"""
    bhashini_service = get_bhashini_service()
    return {
        "languages": bhashini_service.get_supported_languages()
    }
