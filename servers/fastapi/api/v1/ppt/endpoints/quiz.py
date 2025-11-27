"""
API endpoints for quiz generation from presentation slides
"""
import uuid
from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from models.quiz_models import (
    GenerateQuizRequest,
    QuizResponse,
    QuizData
)
from services.database import get_async_session
from services.quiz_service import quiz_service


QUIZ_ROUTER = APIRouter(prefix="/quiz", tags=["Quiz"])


@QUIZ_ROUTER.post("/generate", response_model=QuizResponse)
async def generate_quiz_from_presentation(
    request: Annotated[GenerateQuizRequest, Body()],
    sql_session: AsyncSession = Depends(get_async_session),
):
    """
    Generate quiz questions from presentation slides
    
    This endpoint:
    1. Fetches specified slides from the presentation
    2. Extracts text content from slides
    3. Uses Groq LLM to generate quiz questions
    4. Returns quiz with questions, options, answers, and explanations
    
    Args:
        request: Quiz generation request with presentation_id, slide range, difficulty, etc.
        
    Returns:
        QuizResponse with generated quiz data
    """
    
    try:
        # Parse presentation ID
        presentation_id = uuid.UUID(request.presentation_id)
        
        # Fetch presentation
        presentation = await sql_session.get(PresentationModel, presentation_id)
        if not presentation:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        # Determine slide range
        slide_end = request.slide_end if request.slide_end else request.slide_start
        
        if slide_end < request.slide_start:
            raise HTTPException(
                status_code=400,
                detail="slide_end must be greater than or equal to slide_start"
            )
        
        # Fetch slides in the specified range
        slides_result = await sql_session.execute(
            select(SlideModel)
            .where(
                SlideModel.presentation == presentation_id,
                SlideModel.index >= request.slide_start - 1,  # Convert to 0-indexed
                SlideModel.index <= slide_end - 1
            )
            .order_by(SlideModel.index)
        )
        slides = slides_result.scalars().all()
        
        if not slides:
            raise HTTPException(
                status_code=404,
                detail=f"No slides found in range {request.slide_start}-{slide_end}"
            )
        
        # Extract slide content
        slides_data = [slide.content for slide in slides]
        
        # Generate text content from slides
        content = quiz_service.extract_slide_text_from_data(slides_data)
        
        if not content or len(content.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Insufficient content in slides to generate quiz. Please select slides with more text content."
            )
        
        # Generate quiz using the service
        quiz_data = await quiz_service.generate_quiz(
            content=content,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        
        # Return response
        return QuizResponse(
            success=True,
            quiz_data=QuizData(**quiz_data),
            error=None,
            slide_range=f"{request.slide_start}-{slide_end}",
            num_questions=len(quiz_data.get("quiz", [])),
            difficulty=request.difficulty
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return QuizResponse(
            success=False,
            quiz_data=None,
            error=str(e),
            slide_range=f"{request.slide_start}-{request.slide_end or request.slide_start}",
            num_questions=0,
            difficulty=request.difficulty
        )


@QUIZ_ROUTER.get("/health")
async def health_check():
    """Health check endpoint for quiz service"""
    return {
        "status": "healthy",
        "service": "quiz_generation",
        "version": "1.0.0"
    }
