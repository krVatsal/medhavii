from datetime import datetime
from typing import Optional
from models.llm_message import LLMSystemMessage, LLMUserMessage
from models.presentation_layout import SlideLayoutModel
from models.sql.slide import SlideModel
from services.llm_client import LLMClient
from services.web_search_service import WEB_SEARCH_SERVICE
from utils.llm_client_error_handler import handle_llm_client_exceptions
from utils.llm_provider import get_model
from utils.schema_utils import add_field_in_schema, remove_fields_from_schema


def get_system_prompt(
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
):
    return f"""
    Edit Slide data and speaker note based on provided prompt, follow mentioned steps and notes and provide structured output.

    {"# User Instruction:" if instructions else ""}
    {instructions or ""}

    {"# Tone:" if tone else ""}
    {tone or ""}

    {"# Verbosity:" if verbosity else ""}
    {verbosity or ""}

    # Notes
    - Provide output in language mentioned in **Input**.
    - The goal is to change Slide data based on the provided prompt.
    - Do not change **Image prompts** and **Icon queries** if not asked for in prompt.
    - Generate **Image prompts** and **Icon queries** if asked to generate or change in prompt.
    - Make sure to follow language guidelines.
    - Speaker note should be normal text, not markdown.
    - Speaker note should be simple, clear, concise and to the point.

    **Go through all notes and steps and make sure they are followed, including mentioned constraints**
    """


def get_user_prompt(prompt: str, slide_data: dict, language: str, web_context: Optional[str] = None):
    lines = [
        "## Icon Query And Image Prompt Language",
        "English",
        "",
        "## Current Date and Time",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "",
        "## Slide Content Language",
        language,
        "",
        "## Prompt",
        prompt,
        "",
        "## Slide data",
        str(slide_data),
    ]
    
    if web_context:
        lines.extend(["", "## Web Findings", web_context])
    
    return "\n".join(lines)


def get_messages(
    prompt: str,
    slide_data: dict,
    language: str,
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
    web_context: Optional[str] = None,
):
    return [
        LLMSystemMessage(
            content=get_system_prompt(tone, verbosity, instructions),
        ),
        LLMUserMessage(
            content=get_user_prompt(prompt, slide_data, language, web_context),
        ),
    ]


async def get_edited_slide_content(
    prompt: str,
    slide: SlideModel,
    language: str,
    slide_layout: SlideLayoutModel,
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
    query: Optional[str] = None,
):
    # Get web context for edit
    web_context = ""
    if query:
        try:
            print(f"[WEB SEARCH] Fetching context for slide edit: {query[:100]}")
            web_results = await WEB_SEARCH_SERVICE.search(query)
            web_context = WEB_SEARCH_SERVICE.results_to_text(web_results)
            print(f"[WEB SEARCH] Edit context: {len(web_results)} results")
        except Exception as exc:
            print(f"[WEB SEARCH] Edit search failed: {exc}")
    
    model = get_model()

    response_schema = remove_fields_from_schema(
        slide_layout.json_schema, ["__image_url__", "__icon_url__"]
    )
    response_schema = add_field_in_schema(
        response_schema,
        {
            "__speaker_note__": {
                "type": "string",
                "minLength": 60,
                "maxLength": 250,
                "description": "Speaker note for the slide",
            }
        },
        True,
    )

    client = LLMClient()
    try:
        response = await client.generate_structured(
            model=model,
            messages=get_messages(
                prompt, slide.content, language, tone, verbosity, instructions, web_context
            ),
            response_format=response_schema,
            strict=False,
        )
        return response

    except Exception as e:
        raise handle_llm_client_exceptions(e)
