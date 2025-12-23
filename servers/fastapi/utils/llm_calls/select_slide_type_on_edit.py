from typing import Optional
from models.llm_message import LLMSystemMessage, LLMUserMessage
from models.presentation_layout import PresentationLayoutModel, SlideLayoutModel
from models.slide_layout_index import SlideLayoutIndex
from models.sql.slide import SlideModel
from services.llm_client import LLMClient
from services.web_search_service import WEB_SEARCH_SERVICE
from utils.llm_client_error_handler import handle_llm_client_exceptions
from utils.llm_provider import get_model


def get_messages(
    prompt: str,
    slide_data: dict,
    layout: PresentationLayoutModel,
    current_slide_layout: int,
    web_context: Optional[str] = None,
):
    user_content = f"""
                - User Prompt: {prompt}
                - Current Slide Data: {slide_data}
                - Current Slide Layout: {current_slide_layout}
            """

    if web_context:
        user_content += f"\n- Web Findings: {web_context}"

    return [
        LLMSystemMessage(
            content=f"""
                Select a Slide Layout index based on provided user prompt and current slide data.
                {layout.to_string()}

                # Notes
                - Do not select different slide layout than current unless absolutely necessary as per user prompt. 
                - If user prompt is not clear, select the layout that is most relevant to the slide data.
                - If user prompt is not clear, select the layout that is most relevant to the slide data.
                **Go through all notes and steps and make sure they are followed, including mentioned constraints**
            """,
        ),
        LLMUserMessage(
            content=user_content,
        ),
    ]


async def get_slide_layout_from_prompt(
    prompt: str,
    layout: PresentationLayoutModel,
    slide: SlideModel,
    query: Optional[str] = None,
) -> SlideLayoutModel:

    client = LLMClient()
    model = get_model()

    slide_layout_index = layout.get_slide_layout_index(slide.layout)
    
    # Get web context for layout selection
    web_context = ""
    if query:
        try:
            print(f"[WEB SEARCH] Fetching context for layout selection: {query[:100]}")
            web_results = await WEB_SEARCH_SERVICE.search(query)
            web_context = WEB_SEARCH_SERVICE.results_to_text(web_results)
            print(f"[WEB SEARCH] Layout context: {len(web_results)} results")
        except Exception as exc:
            print(f"[WEB SEARCH] Layout selection search failed: {exc}")

    try:
        response = await client.generate_structured(
            model=model,
            messages=get_messages(
                prompt,
                slide.content,
                layout,
                slide_layout_index,
                web_context,
            ),
            response_format=SlideLayoutIndex.model_json_schema(),
            strict=True,
        )
        index = SlideLayoutIndex(**response).index
        return layout.slides[index]

    except Exception as e:
        raise handle_llm_client_exceptions(e)
