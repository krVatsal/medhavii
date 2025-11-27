"""
Models for quiz generation requests and responses
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    """Single quiz question with options and answer"""
    question: str = Field(..., description="The quiz question text")
    options: List[str] = Field(..., description="List of answer options (A, B, C, D format)")
    correct_answer: str = Field(..., description="The correct answer (A, B, C, or D)")
    explanation: str = Field(..., description="Explanation for the correct answer")


class QuizData(BaseModel):
    """Quiz data containing all questions"""
    quiz: List[QuizQuestion] = Field(..., description="List of quiz questions")


class GenerateQuizRequest(BaseModel):
    """Request model for quiz generation from presentation slides"""
    presentation_id: str = Field(..., description="UUID of the presentation")
    slide_start: int = Field(1, ge=1, description="Starting slide number (1-indexed)")
    slide_end: Optional[int] = Field(None, ge=1, description="Ending slide number (1-indexed). If not provided, uses slide_start")
    num_questions: int = Field(5, ge=1, le=10, description="Number of questions to generate (1-10)")
    difficulty: Literal["easy", "medium", "hard"] = Field("medium", description="Difficulty level of questions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "presentation_id": "123e4567-e89b-12d3-a456-426614174000",
                "slide_start": 1,
                "slide_end": 5,
                "num_questions": 5,
                "difficulty": "medium"
            }
        }


class GenerateQuizFromFileRequest(BaseModel):
    """Request model for quiz generation from uploaded file"""
    file_path: str = Field(..., description="Path to the PPT/PPTX file")
    slide_start: int = Field(1, ge=1, description="Starting slide number (1-indexed)")
    slide_end: int = Field(..., ge=1, description="Ending slide number (1-indexed)")
    num_questions: int = Field(5, ge=1, le=10, description="Number of questions to generate (1-10)")
    difficulty: Literal["easy", "medium", "hard"] = Field("medium", description="Difficulty level of questions")


class QuizResponse(BaseModel):
    """Response model for quiz generation"""
    success: bool = Field(..., description="Whether quiz generation was successful")
    quiz_data: Optional[QuizData] = Field(None, description="Generated quiz data")
    error: Optional[str] = Field(None, description="Error message if generation failed")
    slide_range: str = Field(..., description="Range of slides used for quiz generation")
    num_questions: int = Field(..., description="Number of questions generated")
    difficulty: str = Field(..., description="Difficulty level used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "quiz_data": {
                    "quiz": [
                        {
                            "question": "What is the main topic of this presentation?",
                            "options": [
                                "A) Machine Learning",
                                "B) Data Science",
                                "C) Artificial Intelligence",
                                "D) Deep Learning"
                            ],
                            "correct_answer": "C",
                            "explanation": "The presentation focuses on Artificial Intelligence as the main topic."
                        }
                    ]
                },
                "slide_range": "1-5",
                "num_questions": 5,
                "difficulty": "medium",
                "error": None
            }
        }
