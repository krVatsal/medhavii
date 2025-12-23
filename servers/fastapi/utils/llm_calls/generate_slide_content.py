from datetime import datetime
from typing import Optional
from models.llm_message import LLMSystemMessage, LLMUserMessage
from models.presentation_layout import SlideLayoutModel
from models.presentation_outline_model import SlideOutlineModel
from services.llm_client import LLMClient
from utils.llm_client_error_handler import handle_llm_client_exceptions
from utils.llm_provider import get_model
from utils.schema_utils import add_field_in_schema, remove_fields_from_schema


def get_system_prompt(
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
):
    lines = [
        "Generate structured slide based on provided outline, follow mentioned steps and notes and provide structured output.",
        "",
    ]

    if instructions:
        lines.extend(["# User Instructions:", instructions, ""])

    if tone:
        lines.extend(["# Tone:", tone, ""])

    if verbosity:
        lines.extend(["# Verbosity:", verbosity, ""])

    lines.extend(
        [
            "# Steps",
            "1. Analyze the outline.",
            "2. Generate structured slide based on the outline.",
            "3. Generate speaker note that is simple, clear, concise and to the point.",
            "",
            "# Notes",
            '- Slide body should not use words like "This slide", "This presentation".',
            "- Rephrase the slide body to make it flow naturally.",
            "- Only use markdown to highlight important points.",
            "- Make sure to follow language guidelines.",
            "- Ground the content using any provided web findings instead of guessing facts.",
            "- Speaker note should be normal text, not markdown.",
            "- Strictly follow the max and min character limit for every property in the slide.",
            "- Never ever go over the max character limit. Limit your narration to make sure you never go over the max character limit.",
            "- Number of items should not be more than max number of items specified in slide schema. If you have to put multiple points then merge them to obey max numebr of items.",
            "- Generate content as per the given tone.",
            "- Be very careful with number of words to generate for given field. As generating more than max characters will overflow in the design. So, analyze early and never generate more characters than allowed.",
            "- Do not add emoji in the content.",
            "- Metrics should be in abbreviated form with least possible characters. Do not add long sequence of words for metrics.",
            "- For verbosity:",
            "    - If verbosity is 'concise', then generate description as 1/3 or lower of the max character limit. Don't worry if you miss content or context.",
            "    - If verbosity is 'standard', then generate description as 2/3 of the max character limit.",
            "    - If verbosity is 'text-heavy', then generate description as 3/4 or higher of the max character limit. Make sure it does not exceed the max character limit.",
            "",
            "User instructions, tone and verbosity should always be followed and should supercede any other instruction, except for max and min character limit, slide schema and number of items.",
            "",
            "- Provide output in json format and **don't include <parameters> tags**.",
            "",
            "# CRITICAL JSON Rules",
            "- ALL numeric values MUST be actual numbers, NOT mathematical expressions.",
            '- WRONG: "x": -0.707*2 + 0.707*3  (this is invalid JSON!)',
            '- CORRECT: "x": 0.707  (pre-compute the value)',
            "- If you need to show a calculation, put it in a description string, not as a numeric value.",
            "- For chartData, always use pre-computed literal numbers like 1.5, -2.3, etc.",
            "",
            "# Image and Icon Output Format",
            "image: {",
            "    __image_prompt__: string,",
            "}",
            "icon: {",
            "    __icon_query__: string,",
            "}",
            "video: {",
            "    __video_prompt__: string,",
            "}",
            "",
            "# Video Generation (IMPORTANT)",
            "- For slides about physics (motion, forces, waves, oscillations), mathematics (graphs, transformations), or any dynamic process, YOU MUST include a 'video' object with a '__video_prompt__' field.",
            "- The video prompt should describe an animation suitable for Manim (Mathematical Animation Engine).",
            "- Example: If the slide is about 'Simple Harmonic Motion', add: \"video\": {\"__video_prompt__\": \"Animate a mass-spring system oscillating back and forth\"}",
            "",
        ]
    )

    return "\n".join(lines)


def get_user_prompt(
    outline: str, language: str, web_context: Optional[str] = None
):
    lines = [
        "## Current Date and Time",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "",
        "## Icon Query And Image Prompt Language",
        "English",
        "",
        "## Slide Content Language",
        language,
        "",
        "## Slide Outline",
        outline,
    ]

    if web_context:
        lines.extend(["", "## Web Findings", web_context])

    return "\n".join(lines)


def get_messages(
    outline: str,
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
            content=get_user_prompt(outline, language, web_context),
        ),
    ]


async def get_slide_content_from_type_and_outline(
    slide_layout: SlideLayoutModel,
    outline: SlideOutlineModel,
    language: str,
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
    web_context: Optional[str] = None,
):
    client = LLMClient()
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
    
    response_schema = add_field_in_schema(
        response_schema,
        {
            "video": {
                "type": "object",
                "description": "Video animation for the slide. Use this if the content involves mathematical concepts, physics simulations, or dynamic processes.",
                "properties": {
                    "__video_prompt__": {
                        "type": "string",
                        "description": "Prompt for generating a video animation using Manim. Describe the animation in detail.",
                    }
                },
                "required": ["__video_prompt__"]
            }
        },
        False,
    )

    try:
        response = await client.generate_structured(
            model=model,
            messages=get_messages(
                outline.content,
                language,
                tone,
                verbosity,
                instructions,
                web_context,
            ),
            response_format=response_schema,
            strict=False,
        )
        # Debug: Check if video field is in the response
        if "video" in response:
            print(f"[SLIDE CONTENT] Video field found: {response.get('video')}")
        else:
            print(f"[SLIDE CONTENT] No video field in response. Keys: {list(response.keys())}")
        return response

    except Exception as e:
        raise handle_llm_client_exceptions(e)
