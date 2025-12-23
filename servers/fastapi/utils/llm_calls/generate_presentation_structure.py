from typing import Optional
from models.llm_message import LLMSystemMessage, LLMUserMessage
from models.presentation_layout import PresentationLayoutModel
from models.presentation_outline_model import PresentationOutlineModel
from services.llm_client import LLMClient
from services.web_search_service import WEB_SEARCH_SERVICE
from utils.llm_client_error_handler import handle_llm_client_exceptions
from utils.llm_provider import get_model
from utils.get_dynamic_models import get_presentation_structure_model_with_n_slides
from models.presentation_structure_model import PresentationStructureModel


def get_messages(
    presentation_layout: PresentationLayoutModel,
    n_slides: int,
    data: str,
    instructions: Optional[str] = None,
    web_context: Optional[str] = None,
):
    return [
        LLMSystemMessage(
            content=f"""
                You're a professional presentation designer with creative freedom to design engaging presentations.

                {presentation_layout.to_string()}

                # DESIGN PHILOSOPHY
                - Create visually compelling and varied presentations
                - Match layout to content purpose and audience needs
                - Prioritize engagement over rigid formatting rules

                # Layout Selection Guidelines
                1. **Content-driven choices**: Let the slide's purpose guide layout selection
                - Opening/closing → Title layouts
                - Processes/workflows → Visual process layouts  
                - Comparisons/contrasts → Side-by-side layouts
                - Data/metrics → Chart/graph layouts
                - Concepts/ideas → Image + text layouts
                - Key insights → Emphasis layouts

                2. **Visual variety**: Aim for diverse, engaging presentation flow
                - Mix text-heavy and visual-heavy slides naturally
                - Use your judgment on when repetition serves the content
                - Balance information density across slides

                3. **Audience experience**: Consider how slides work together
                - Create natural transitions between topics
                - Use layouts that enhance comprehension
                - Design for maximum impact and retention

                **Trust your design instincts. Focus on creating the most effective presentation for the content and audience.**

                {"# User Instruction:" if instructions else ""}
                {instructions or ""}

                User intruction should be taken into account while creating the presentation structure, except for number of slides.

                Select layout index for each of the {n_slides} slides based on what will best serve the presentation's goals.
            """,
        ),
        LLMUserMessage(
            content=f"""
                {data}
            """,
        ),
    ]


def get_messages_for_slides_markdown(
    presentation_layout: PresentationLayoutModel,
    n_slides: int,
    data: str,
    instructions: Optional[str] = None,
):
    return [
        LLMSystemMessage(
            content=f"""
                You're a professional presentation designer with creative freedom to design engaging presentations.

                {"# User Instruction:" if instructions else ""}
                {instructions or ""}

                {presentation_layout.to_string()}

                Select layout that best matches the content of the slides.

                User intruction should be taken into account while creating the presentation structure, except for number of slides.

                Select layout index for each of the {n_slides} slides based on what will best serve the presentation's goals.
            """,
        ),
        LLMUserMessage(
            content=f"""
                {data}
            """,
        ),
    ]


async def generate_presentation_structure(
    presentation_outline: PresentationOutlineModel,
    presentation_layout: PresentationLayoutModel,
    instructions: Optional[str] = None,
    using_slides_markdown: bool = False,
    query: Optional[str] = None,
) -> PresentationStructureModel:

    client = LLMClient()
    model = get_model()
    response_model = get_presentation_structure_model_with_n_slides(
        len(presentation_outline.slides)
    )

    # Get web context for structure generation
    web_context = ""
    if query:
        try:
            print(f"[WEB SEARCH] Fetching context for structure generation: {query[:100]}")
            web_results = await WEB_SEARCH_SERVICE.search(query)
            web_context = WEB_SEARCH_SERVICE.results_to_text(web_results)
            print(f"[WEB SEARCH] Structure context: {len(web_results)} results")
        except Exception as exc:
            print(f"[WEB SEARCH] Structure search failed: {exc}")

    try:
        response = await client.generate_structured(
            model=model,
            messages=(
                get_messages_for_slides_markdown(
                    presentation_layout,
                    len(presentation_outline.slides),
                    presentation_outline.to_string(),
                    instructions,
                )
                if using_slides_markdown
                else get_messages(
                    presentation_layout,
                    len(presentation_outline.slides),
                    presentation_outline.to_string(),
                    instructions,
                    web_context,
                )
            ),
            response_format=response_model.model_json_schema(),
            strict=True,
        )
        return PresentationStructureModel(**response)
    except Exception as e:
        raise handle_llm_client_exceptions(e)
