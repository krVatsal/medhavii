"""
Models for voice narration feature using Bhashini API
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class TeachingScript(BaseModel):
    """Teaching-style script for a single slide"""
    slide_index: int = Field(description="Index of the slide")
    teaching_explanation: str = Field(
        description="Detailed teaching-style explanation with examples and regional context",
        min_length=50
    )
    estimated_duration_seconds: float = Field(
        description="Estimated time to read this script in seconds",
        gt=0
    )
    key_concepts: List[str] = Field(
        description="Key concepts covered in this explanation",
        default_factory=list
    )


class VoiceNarrationRequest(BaseModel):
    """Request model for generating voice narration"""
    presentation_id: str = Field(description="ID of the presentation")
    language_code: str = Field(
        description="Bhashini language code (e.g., 'hi', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml', 'pa', 'or')",
        default="hi"
    )
    voice_gender: str = Field(
        description="Voice gender preference",
        default="female",
        pattern="^(male|female)$"
    )
    include_regional_references: bool = Field(
        description="Include region-specific examples and references",
        default=True
    )
    student_level: str = Field(
        description="Target student level for explanation complexity",
        default="intermediate",
        pattern="^(beginner|intermediate|advanced)$"
    )


class SlideNarration(BaseModel):
    """Generated narration for a single slide"""
    slide_index: int
    script: str = Field(description="Teaching script text")
    audio_url: str = Field(description="URL to the generated audio file")
    duration_seconds: float = Field(description="Duration of the audio in seconds")
    language: str = Field(description="Language code used")


class PresentationNarration(BaseModel):
    """Complete narration for a presentation"""
    presentation_id: str
    slides: List[SlideNarration] = Field(description="Narration for each slide")
    total_duration_seconds: float = Field(description="Total presentation duration")
    language: str = Field(description="Language code used")
    created_at: Optional[str] = None


class BhashiniTTSRequest(BaseModel):
    """Request model for Bhashini TTS API"""
    text: str = Field(description="Text to convert to speech")
    source_language: str = Field(description="Source language code")
    gender: str = Field(description="Voice gender", default="female")


class BhashiniTTSResponse(BaseModel):
    """Response model from Bhashini TTS API"""
    audio_content: str = Field(description="Base64 encoded audio content")
    audio_uri: Optional[str] = Field(description="URI to the audio file", default=None)
