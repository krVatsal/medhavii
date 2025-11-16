"""
Service to generate teaching-style explanations for presentation slides using LLM
"""
import json
from typing import List, Optional
from models.voice_narration_models import TeachingScript
from models.sql.slide import SlideModel
from services.llm_client import get_llm_response
from utils.llm_provider import get_model
from constants.regional_context import get_regional_prompt_enhancement


async def generate_teaching_script(
    slide: SlideModel,
    language: str = "English",
    student_level: str = "intermediate",
    include_regional_references: bool = True,
    presentation_context: Optional[str] = None
) -> TeachingScript:
    """
    Generate a detailed teaching-style explanation for a slide
    
    Args:
        slide: The slide model containing content
        language: Target language for the explanation
        student_level: Student level (beginner/intermediate/advanced)
        include_regional_references: Whether to include regional examples
        presentation_context: Overall presentation context for better continuity
    
    Returns:
        TeachingScript with detailed explanation
    """
    
    # Extract slide content as text
    slide_content = _extract_slide_text_content(slide.content)
    speaker_note = slide.speaker_note or ""
    
    # Build the prompt for teaching script generation
    regional_context = ""
    if include_regional_references:
        # Get language code from full language name (e.g., "Hindi" -> "hi")
        language_code_map = {
            "Hindi": "hi", "Bengali": "bn", "Tamil": "ta", "Telugu": "te",
            "Marathi": "mr", "Gujarati": "gu", "Kannada": "kn", "Malayalam": "ml",
            "Punjabi": "pa", "Odia": "or", "English": "en"
        }
        lang_code = language_code_map.get(language, "en")
        regional_context = get_regional_prompt_enhancement(lang_code)
    
    system_prompt = f"""You are an expert teacher creating audio narration scripts for educational presentations.
Your goal is to explain the slide content in a clear, engaging, and student-friendly manner.

Key requirements:
1. Provide detailed explanations, not just reading the slide text
2. Include examples and analogies to illustrate concepts
3. Use conversational, friendly tone suitable for audio narration
4. Add context and connections to real-world applications
5. Explain WHY things matter, not just WHAT they are
6. Keep the student level in mind: {student_level}
7. Language: {language}
{regional_context if regional_context else ''}

The script should sound natural when spoken aloud and help students truly understand the concept."""

    user_prompt = f"""Generate a teaching-style audio narration script for this slide.

Slide Content:
{slide_content}

{f"Speaker Notes: {speaker_note}" if speaker_note else ""}

{f"Presentation Context: {presentation_context}" if presentation_context else ""}

Create a comprehensive teaching script that:
1. Introduces the topic naturally
2. Explains each key point with examples
3. Provides analogies or real-world connections
4. Emphasizes important concepts
5. Concludes with a smooth transition (if not the last slide)

The script should be detailed enough to take 30-90 seconds to read aloud.
Respond in JSON format with this structure:
{{
    "teaching_explanation": "Your detailed teaching script here...",
    "estimated_duration_seconds": 45.0,
    "key_concepts": ["concept1", "concept2", "concept3"]
}}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    model = get_model()
    response = await get_llm_response(
        messages=messages,
        model=model,
        response_format="json"
    )
    
    # Parse the response
    try:
        script_data = json.loads(response)
        return TeachingScript(
            slide_index=slide.index,
            teaching_explanation=script_data["teaching_explanation"],
            estimated_duration_seconds=script_data.get("estimated_duration_seconds", 45.0),
            key_concepts=script_data.get("key_concepts", [])
        )
    except (json.JSONDecodeError, KeyError) as e:
        # Fallback: use the response as-is
        return TeachingScript(
            slide_index=slide.index,
            teaching_explanation=response,
            estimated_duration_seconds=len(response.split()) / 2.5,  # Rough estimate: 150 words/minute
            key_concepts=[]
        )


def _extract_slide_text_content(content: dict) -> str:
    """
    Recursively extract all text content from slide content dictionary
    
    Args:
        content: Slide content dictionary
    
    Returns:
        String with all text content
    """
    text_parts = []
    
    def extract_recursive(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ["text", "title", "heading", "subtitle", "content", "description"]:
                    if isinstance(value, str):
                        text_parts.append(value)
                else:
                    extract_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_recursive(item)
        elif isinstance(obj, str):
            text_parts.append(obj)
    
    extract_recursive(content)
    return "\n".join(filter(None, text_parts))


async def generate_teaching_scripts_for_presentation(
    slides: List[SlideModel],
    language: str = "English",
    student_level: str = "intermediate",
    include_regional_references: bool = True,
    presentation_title: Optional[str] = None
) -> List[TeachingScript]:
    """
    Generate teaching scripts for all slides in a presentation
    
    Args:
        slides: List of slide models
        language: Target language
        student_level: Student level
        include_regional_references: Include regional examples
        presentation_title: Title of the presentation for context
    
    Returns:
        List of TeachingScript objects
    """
    scripts = []
    presentation_context = f"This is part of a presentation about: {presentation_title}" if presentation_title else None
    
    for slide in slides:
        script = await generate_teaching_script(
            slide=slide,
            language=language,
            student_level=student_level,
            include_regional_references=include_regional_references,
            presentation_context=presentation_context
        )
        scripts.append(script)
    
    return scripts
