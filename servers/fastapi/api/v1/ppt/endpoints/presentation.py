import asyncio
from datetime import datetime
import json
import math
import os
import random
import traceback
import logging
from typing import Annotated, List, Literal, Optional, Tuple
import dirtyjson
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Path
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlmodel import select
from constants.presentation import DEFAULT_TEMPLATES
from enums.webhook_event import WebhookEvent
from models.api_error_model import APIErrorModel
from models.generate_presentation_request import GeneratePresentationRequest
from models.presentation_and_path import PresentationPathAndEditPath
from models.presentation_from_template import EditPresentationRequest
from models.presentation_outline_model import (
    PresentationOutlineModel,
    SlideOutlineModel,
)
from enums.tone import Tone
from enums.verbosity import Verbosity
from models.pptx_models import PptxPresentationModel
from models.presentation_layout import PresentationLayoutModel
from models.presentation_structure_model import PresentationStructureModel
from models.presentation_with_slides import (
    PresentationWithSlides,
)
from models.sql.template import TemplateModel
from models.llm_message import (
    LLMSystemMessage,
    LLMUserMessage,
    OpenAIAssistantMessage,
)

from services.documents_loader import DocumentsLoader
from services.webhook_service import WebhookService
from utils.get_layout_by_name import get_layout_by_name
from services.image_generation_service import ImageGenerationService
from utils.dict_utils import deep_update, get_dict_at_path, set_dict_at_path
from utils.export_utils import export_presentation
from utils.llm_calls.generate_presentation_outlines import generate_ppt_outline
from models.sql.slide import SlideModel
from models.sse_response import SSECompleteResponse, SSEErrorResponse, SSEResponse

from services.database import get_async_session, async_session_maker
from services.llm_client import LLMClient
from services.temp_file_service import TEMP_FILE_SERVICE
from services.concurrent_service import CONCURRENT_SERVICE
from models.sql.presentation import PresentationModel
from services.manim_service import MANIM_SERVICE
from services.pptx_presentation_creator import PptxPresentationCreator
from services.web_search_service import WEB_SEARCH_SERVICE
from models.sql.async_presentation_generation_status import (
    AsyncPresentationGenerationTaskModel,
)
from utils.asset_directory_utils import get_exports_directory, get_images_directory
from utils.get_env import get_app_data_directory_env
from utils.llm_calls.generate_presentation_structure import (
    generate_presentation_structure,
)
from utils.llm_calls.generate_slide_content import (
    get_slide_content_from_type_and_outline,
)
from utils.llm_provider import get_model
from utils.ppt_utils import (
    get_presentation_title_from_outlines,
    select_toc_or_list_slide_layout_index,
)
from utils.process_slides import (
    process_slide_add_placeholder_assets,
    process_slide_and_fetch_assets,
)
import uuid
import json


PRESENTATION_ROUTER = APIRouter(prefix="/presentation", tags=["Presentation"])
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


class PresentationChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class PresentationChatRequest(BaseModel):
    presentation_id: uuid.UUID
    messages: List[PresentationChatMessage]


class PresentationChatResponse(BaseModel):
    reply: str


@PRESENTATION_ROUTER.get("/all", response_model=List[PresentationWithSlides])
async def get_all_presentations(sql_session: AsyncSession = Depends(get_async_session)):
    presentations_with_slides = []

    query = (
        select(PresentationModel, SlideModel)
        .join(
            SlideModel,
            (SlideModel.presentation == PresentationModel.id) & (SlideModel.index == 0),
        )
        .order_by(PresentationModel.created_at.desc())
    )

    results = await sql_session.execute(query)
    rows = results.all()
    presentations_with_slides = [
        PresentationWithSlides(
            **presentation.model_dump(),
            slides=[first_slide],
        )
        for presentation, first_slide in rows
    ]
    return presentations_with_slides


@PRESENTATION_ROUTER.get("/{id}", response_model=PresentationWithSlides)
async def get_presentation(
    id: uuid.UUID, sql_session: AsyncSession = Depends(get_async_session)
):
    presentation = await sql_session.get(PresentationModel, id)
    if not presentation:
        raise HTTPException(404, "Presentation not found")
    slides = await sql_session.scalars(
        select(SlideModel)
        .where(SlideModel.presentation == id)
        .order_by(SlideModel.index)
    )
    return PresentationWithSlides(
        **presentation.model_dump(),
        slides=slides,
    )


@PRESENTATION_ROUTER.delete("/{id}", status_code=204)
async def delete_presentation(
    id: uuid.UUID, sql_session: AsyncSession = Depends(get_async_session)
):
    presentation = await sql_session.get(PresentationModel, id)
    if not presentation:
        raise HTTPException(404, "Presentation not found")

    await sql_session.delete(presentation)
    await sql_session.commit()


@PRESENTATION_ROUTER.post("/create", response_model=PresentationModel)
async def create_presentation(
    content: Annotated[str, Body()],
    n_slides: Annotated[int, Body()],
    language: Annotated[str, Body()],
    file_paths: Annotated[Optional[List[str]], Body()] = None,
    tone: Annotated[Tone, Body()] = Tone.DEFAULT,
    verbosity: Annotated[Verbosity, Body()] = Verbosity.STANDARD,
    instructions: Annotated[Optional[str], Body()] = None,
    include_table_of_contents: Annotated[bool, Body()] = False,
    include_title_slide: Annotated[bool, Body()] = True,
    sql_session: AsyncSession = Depends(get_async_session),
):

    if include_table_of_contents and n_slides < 3:
        raise HTTPException(
            status_code=400,
            detail="Number of slides cannot be less than 3 if table of contents is included",
        )

    presentation_id = uuid.uuid4()
    print("[WEB SEARCH DEBUG] Creating presentation with web_search=True")

    presentation = PresentationModel(
        id=presentation_id,
        content=content,
        n_slides=n_slides,
        language=language,
        file_paths=file_paths,
        tone=tone.value,
        verbosity=verbosity.value,
        instructions=instructions,
        include_table_of_contents=include_table_of_contents,
        include_title_slide=include_title_slide,
        web_search=True,
    )

    sql_session.add(presentation)
    await sql_session.commit()

    return presentation

@PRESENTATION_ROUTER.post("/chat", response_model=PresentationChatResponse)
async def chat_with_presentation(
    body: PresentationChatRequest,
    sql_session: AsyncSession = Depends(get_async_session),
):
    presentation = await sql_session.get(PresentationModel, body.presentation_id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    slide_rows = await sql_session.scalars(
        select(SlideModel)
        .where(SlideModel.presentation == body.presentation_id)
        .order_by(SlideModel.index)
    )
    slides = list(slide_rows)
    if not slides:
        raise HTTPException(
            status_code=400,
            detail="No slides found for this presentation",
        )

    context_lines: List[str] = []
    for slide in slides:
        context_lines.append(
            f"Slide {slide.index + 1} ({slide.layout}): {json.dumps(slide.content)}"
        )
        if slide.speaker_note:
            context_lines.append(f"Speaker notes: {slide.speaker_note}")

    system_prompt = """
You are a warm, jolly, and helpful teacher chatting about the user's presentation.
Use the presentation slides below as your source of truth. Be concise, encouraging,
and explain concepts clearly. If something is missing from the slides, say so
instead of inventing details.
""".strip()

    contextual_prompt = (
        f"Presentation title: {presentation.title or 'Untitled'}\n"
        + "\n".join(context_lines)
    )

    llm_messages = [LLMSystemMessage(content=f"{system_prompt}\n\n{contextual_prompt}")]
    for message in body.messages:
        if message.role == "assistant":
            llm_messages.append(
                OpenAIAssistantMessage(content=message.content, tool_calls=[])
            )
        else:
            llm_messages.append(LLMUserMessage(content=message.content))

    client = LLMClient()
    model = get_model()

    try:
        reply = await client.generate(model=model, messages=llm_messages, max_tokens=400)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHAT ERROR] {e}")
        raise HTTPException(
            status_code=500, detail="Unable to chat with this presentation right now"
        )

    return PresentationChatResponse(reply=reply)


@PRESENTATION_ROUTER.post("/prepare", response_model=PresentationModel)
async def prepare_presentation(
    presentation_id: Annotated[uuid.UUID, Body()],
    outlines: Annotated[List[SlideOutlineModel], Body()],
    layout: Annotated[PresentationLayoutModel, Body()],
    title: Annotated[Optional[str], Body()] = None,
    sql_session: AsyncSession = Depends(get_async_session),
):
    if not outlines:
        raise HTTPException(status_code=400, detail="Outlines are required")

    presentation = await sql_session.get(PresentationModel, presentation_id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    presentation_outline_model = PresentationOutlineModel(slides=outlines)

    total_slide_layouts = len(layout.slides)
    total_outlines = len(outlines)

    if layout.ordered:
        presentation_structure = layout.to_presentation_structure()
    else:
        presentation_structure: PresentationStructureModel = (
            await generate_presentation_structure(
                presentation_outline=presentation_outline_model,
                presentation_layout=layout,
                instructions=presentation.instructions,
                query=presentation.content or presentation.topic,
            )
        )

    presentation_structure.slides = presentation_structure.slides[: len(outlines)]
    for index in range(total_outlines):
        random_slide_index = random.randint(0, total_slide_layouts - 1)
        if index >= total_outlines:
            presentation_structure.slides.append(random_slide_index)
            continue
        if presentation_structure.slides[index] >= total_slide_layouts:
            presentation_structure.slides[index] = random_slide_index

    if presentation.include_table_of_contents:
        n_toc_slides = presentation.n_slides - total_outlines
        toc_slide_layout_index = select_toc_or_list_slide_layout_index(layout)
        if toc_slide_layout_index != -1:
            outline_index = 1 if presentation.include_title_slide else 0
            for i in range(n_toc_slides):
                outlines_to = outline_index + 10
                if total_outlines == outlines_to:
                    outlines_to -= 1

                presentation_structure.slides.insert(
                    i + 1 if presentation.include_title_slide else i,
                    toc_slide_layout_index,
                )
                toc_outline = f"Table of Contents\n\n"

                for outline in presentation_outline_model.slides[
                    outline_index:outlines_to
                ]:
                    page_number = (
                        outline_index - i + n_toc_slides + 1
                        if presentation.include_title_slide
                        else outline_index - i + n_toc_slides
                    )
                    toc_outline += f"Slide page number: {page_number}\n Slide Content: {outline.content[:100]}\n\n"
                    outline_index += 1

                outline_index += 1

                presentation_outline_model.slides.insert(
                    i + 1 if presentation.include_title_slide else i,
                    SlideOutlineModel(
                        content=toc_outline,
                    ),
                )

    sql_session.add(presentation)
    presentation.outlines = presentation_outline_model.model_dump(mode="json")
    presentation.title = title or presentation.title
    presentation.set_layout(layout)
    presentation.set_structure(presentation_structure)
    await sql_session.commit()

    return presentation


@PRESENTATION_ROUTER.get("/stream/{id}", response_model=PresentationWithSlides)
async def stream_presentation(
    id: uuid.UUID, sql_session: AsyncSession = Depends(get_async_session)
):
    presentation = await sql_session.get(PresentationModel, id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    if not presentation.structure:
        raise HTTPException(
            status_code=400,
            detail="Presentation not prepared for stream",
        )
    if not presentation.outlines:
        raise HTTPException(
            status_code=400,
            detail="Outlines can not be empty",
        )

    image_generation_service = ImageGenerationService(get_images_directory())

    async def inner():
        structure = presentation.get_structure()
        layout = presentation.get_layout()
        outline = presentation.get_presentation_outline()
        web_context = None
        try:
            logger.warning(
                "[WEB SEARCH] Fetching streaming context",
                extra={
                    "query": presentation.content,
                    "presentation_id": str(presentation.id),
                },
            )
            search_results = await WEB_SEARCH_SERVICE.search(presentation.content)
            web_context = WEB_SEARCH_SERVICE.results_to_text(search_results)
            logger.warning(
                "[WEB SEARCH] Streaming context built",
                extra={
                    "query": presentation.content,
                    "result_count": len(search_results),
                    "context_preview": (web_context or "")[:200],
                    "presentation_id": str(presentation.id),
                },
            )
        except Exception as exc:
            print(f"[WEB SEARCH] Streaming search failed: {exc}")
        # These tasks will be gathered and awaited after all slides are generated
        async_assets_generation_tasks = []
        video_jobs: List[Tuple[uuid.UUID, int, list, str]] = []

        slides: List[SlideModel] = []
        yield SSEResponse(
            event="response",
            data=json.dumps({"type": "chunk", "chunk": '{ "slides": [ '}),
        ).to_string()
        for i, slide_layout_index in enumerate(structure.slides):
            slide_layout = layout.slides[slide_layout_index]

            try:
                slide_content = await get_slide_content_from_type_and_outline(
                    slide_layout,
                    outline.slides[i],
                    presentation.language,
                    presentation.tone,
                    presentation.verbosity,
                    presentation.instructions,
                    web_context,
                )
            except HTTPException as e:
                yield SSEErrorResponse(detail=e.detail).to_string()
                return

            slide = SlideModel(
                presentation=id,
                layout_group=layout.name,
                layout=slide_layout.id,
                index=i,
                speaker_note=slide_content.get("__speaker_note__", ""),
                content=slide_content,
            )
            slides.append(slide)

            # This will mutate slide and add placeholder assets
            process_slide_add_placeholder_assets(slide)

            # This will mutate slide
            async_assets_generation_tasks.append(
                process_slide_and_fetch_assets(
                    image_generation_service,
                    slide,
                    enable_video_generation=False,
                    video_jobs=video_jobs,
                )
            )

            yield SSEResponse(
                event="response",
                data=json.dumps({"type": "chunk", "chunk": slide.model_dump_json()}),
            ).to_string()

        yield SSEResponse(
            event="response",
            data=json.dumps({"type": "chunk", "chunk": " ] }"}),
        ).to_string()

        generated_assets_lists = await asyncio.gather(*async_assets_generation_tasks)
        generated_assets = []
        for assets_list in generated_assets_lists:
            generated_assets.extend(assets_list)

        # Moved this here to make sure new slides are generated before deleting the old ones
        await sql_session.execute(
            delete(SlideModel).where(SlideModel.presentation == id)
        )
        await sql_session.commit()

        sql_session.add(presentation)
        sql_session.add_all(slides)
        sql_session.add_all(generated_assets)
        await sql_session.commit()

        async def run_video_jobs():
            """Background task to generate and embed videos with proper state tracking."""
            if not video_jobs:
                return
            
            print(f"[VIDEO GEN] Starting background job processing with {len(video_jobs)} queued video(s)")
            
            # Deduplicate jobs by (presentation, slide index) to avoid reruns
            seen = set()
            deduped_jobs = []
            for job in video_jobs:
                key = (job[0], job[1])
                if key in seen:
                    print(f"[VIDEO GEN] Skipping duplicate job for presentation {job[0]}, slide {job[1]}")
                    continue
                seen.add(key)
                deduped_jobs.append(job)
            
            print(f"[VIDEO GEN] After deduplication: {len(deduped_jobs)} unique video job(s) to process")

            async with async_session_maker() as bg_session:
                from models.sql.video_job import VideoJob, VideoJobStatus
                from models.json_path_guide import JsonPathGuide
                from datetime import datetime
                
                app_data_dir = get_app_data_directory_env()
                
                for job_num, (presentation_id, slide_index, video_path_str, prompt) in enumerate(deduped_jobs, 1):
                    print(f"[VIDEO GEN] Processing job {job_num}/{len(deduped_jobs)}: presentation {presentation_id}, slide {slide_index}")
                    
                    # Check if job already exists for this slide
                    # video_path_str is now a JSON string representation of JsonPathGuide
                    existing_job = await bg_session.scalar(
                        select(VideoJob).where(
                            VideoJob.presentation_id == presentation_id,
                            VideoJob.slide_index == slide_index,
                            VideoJob.video_path == video_path_str,
                            VideoJob.status.in_([
                                VideoJobStatus.GENERATING,
                                VideoJobStatus.GENERATED,
                                VideoJobStatus.EMBEDDING,
                                VideoJobStatus.EMBEDDED
                            ])
                        )
                    )
                    
                    if existing_job:
                        print(
                            f"[VIDEO GEN] Skipping slide {slide_index} for presentation {presentation_id}: "
                            f"job already exists with status {existing_job.status}"
                        )
                        continue
                    
                    # Verify slide still exists
                    slide_db = await bg_session.scalar(
                        select(SlideModel).where(
                            SlideModel.presentation == presentation_id,
                            SlideModel.index == slide_index,
                        )
                    )
                    if not slide_db:
                        print(
                            f"[VIDEO GEN] Skipping slide {slide_index} for presentation {presentation_id}: slide not found"
                        )
                        continue

                    # Parse video_path_str back to JsonPathGuide for path operations
                    video_path = JsonPathGuide.model_validate_json(video_path_str)

                    # Check if video already embedded (final check)
                    existing_video_dict = get_dict_at_path(slide_db.content, video_path)
                    existing_url = existing_video_dict.get("__video_url__") if existing_video_dict else None
                    if existing_url and "placeholder" not in str(existing_url):
                        print(
                            f"[VIDEO GEN] Skipping slide {slide_index} for presentation {presentation_id}: already has video URL"
                        )
                        # Mark as EMBEDDED if we find existing video
                        if not existing_job:
                            job_record = VideoJob(
                                presentation_id=presentation_id,
                                slide_index=slide_index,
                                video_path=video_path_str,
                                prompt=prompt,
                                status=VideoJobStatus.EMBEDDED,
                                completed_at=datetime.utcnow()
                            )
                            bg_session.add(job_record)
                            await bg_session.commit()
                        continue

                    # Create job record in PENDING state
                    job_record = VideoJob(
                        presentation_id=presentation_id,
                        slide_index=slide_index,
                        video_path=video_path_str,
                        prompt=prompt,
                        status=VideoJobStatus.PENDING
                    )
                    bg_session.add(job_record)
                    await bg_session.commit()
                    
                    try:
                        # Update status to GENERATING
                        job_record.status = VideoJobStatus.GENERATING
                        job_record.started_at = datetime.utcnow()
                        await bg_session.commit()
                        
                        # Generate video (semaphore handled inside service)
                        video_asset = await MANIM_SERVICE.generate_video(prompt)
                        
                        if not video_asset:
                            job_record.status = VideoJobStatus.FAILED
                            job_record.error_message = "Video generation returned None"
                            job_record.completed_at = datetime.utcnow()
                            await bg_session.commit()
                            continue
                        
                        # Update status to GENERATED
                        job_record.status = VideoJobStatus.GENERATED
                        await bg_session.commit()
                        
                    except Exception as e:
                        print(
                            f"[VIDEO GEN] Video generation failed for slide {slide_index} "
                            f"in presentation {presentation_id}: {type(e).__name__}: {e}"
                        )
                        job_record.status = VideoJobStatus.FAILED
                        job_record.error_message = f"{type(e).__name__}: {str(e)}"
                        job_record.completed_at = datetime.utcnow()
                        await bg_session.commit()
                        continue

                    # === EMBEDDING PHASE (NO semaphore needed - fast operation) ===
                    try:
                        # Update status to EMBEDDING
                        job_record.status = VideoJobStatus.EMBEDDING
                        await bg_session.commit()
                        
                        # Persist video asset
                        bg_session.add(video_asset)
                        await bg_session.flush()
                        
                        # Store asset ID in job record
                        job_record.video_asset_id = video_asset.id
                        await bg_session.commit()

                        # Build video URL
                        video_dict = existing_video_dict or {}
                        if video_asset.path.startswith(app_data_dir):
                            relative_path = os.path.relpath(video_asset.path, app_data_dir)
                            relative_path = relative_path.replace(os.sep, "/")
                            video_dict["__video_url__"] = f"/app_data/{relative_path}"
                        else:
                            video_dict["__video_url__"] = video_asset.path

                        # Update slide content
                        set_dict_at_path(slide_db.content, video_path, video_dict)
                        slide_db.content = slide_db.content
                        bg_session.add(slide_db)
                        
                        # Commit with retries
                        commit_ok = False
                        for attempt in range(3):
                            try:
                                await bg_session.commit()
                                commit_ok = True
                                break
                            except Exception as e:
                                await bg_session.rollback()
                                print(
                                    f"[VIDEO GEN] Failed to commit video embedding for slide {slide_index} "
                                    f"in presentation {presentation_id} (attempt {attempt+1}/3): {type(e).__name__}: {e}"
                                )
                                await asyncio.sleep(0.5 * (attempt + 1))
                        
                        if not commit_ok:
                            print(
                                f"[VIDEO GEN] Giving up embedding video for slide {slide_index} "
                                f"in presentation {presentation_id} after retries"
                            )
                            job_record.status = VideoJobStatus.FAILED
                            job_record.error_message = "Failed to commit video embedding after 3 retries"
                            job_record.completed_at = datetime.utcnow()
                            await bg_session.commit()
                            continue
                        
                        # Mark job as EMBEDDED (SUCCESS!)
                        job_record.status = VideoJobStatus.EMBEDDED
                        job_record.completed_at = datetime.utcnow()
                        await bg_session.commit()
                        
                        # Refresh slide to verify video URL was persisted
                        await bg_session.refresh(slide_db)
                        refreshed_video_dict = get_dict_at_path(slide_db.content, video_path)
                        refreshed_url = refreshed_video_dict.get("__video_url__") if refreshed_video_dict else None
                        
                        print(
                            f"[VIDEO GEN] ✅ Successfully embedded video for slide {slide_index} "
                            f"in presentation {presentation_id}. Video URL: {refreshed_url}"
                        )
                        
                    except Exception as e:
                        print(
                            f"[VIDEO GEN] Video embedding failed for slide {slide_index} "
                            f"in presentation {presentation_id}: {type(e).__name__}: {e}"
                        )
                        job_record.status = VideoJobStatus.FAILED
                        job_record.error_message = f"Embedding error: {type(e).__name__}: {str(e)}"
                        job_record.completed_at = datetime.utcnow()
                        try:
                            await bg_session.commit()
                        except:
                            pass
                        continue

        asyncio.create_task(run_video_jobs())

        response = PresentationWithSlides(
            **presentation.model_dump(),
            slides=slides,
        )

        yield SSECompleteResponse(
            key="presentation",
            value=response.model_dump(mode="json"),
        ).to_string()

    return StreamingResponse(inner(), media_type="text/event-stream")


@PRESENTATION_ROUTER.patch("/update", response_model=PresentationWithSlides)
async def update_presentation(
    id: Annotated[uuid.UUID, Body()],
    n_slides: Annotated[Optional[int], Body()] = None,
    title: Annotated[Optional[str], Body()] = None,
    slides: Annotated[Optional[List[SlideModel]], Body()] = None,
    sql_session: AsyncSession = Depends(get_async_session),
):
    presentation = await sql_session.get(PresentationModel, id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    presentation_update_dict = {}
    if n_slides:
        presentation_update_dict["n_slides"] = n_slides
    if title:
        presentation_update_dict["title"] = title

    if n_slides or title:
        presentation.sqlmodel_update(presentation_update_dict)

    if slides:
        # Just to make sure id is UUID
        for slide in slides:
            slide.presentation = uuid.UUID(slide.presentation)
            slide.id = uuid.UUID(slide.id)

        await sql_session.execute(
            delete(SlideModel).where(SlideModel.presentation == presentation.id)
        )
        sql_session.add_all(slides)

    await sql_session.commit()

    return PresentationWithSlides(
        **presentation.model_dump(),
        slides=slides or [],
    )


@PRESENTATION_ROUTER.post("/export/pptx", response_model=str)
async def export_presentation_as_pptx(
    pptx_model: Annotated[PptxPresentationModel, Body()],
):
    temp_dir = TEMP_FILE_SERVICE.create_temp_dir()

    pptx_creator = PptxPresentationCreator(pptx_model, temp_dir)
    await pptx_creator.create_ppt()

    export_directory = get_exports_directory()
    pptx_path = os.path.join(
        export_directory, f"{pptx_model.name or uuid.uuid4()}.pptx"
    )
    pptx_creator.save(pptx_path)

    return pptx_path


@PRESENTATION_ROUTER.post("/export", response_model=PresentationPathAndEditPath)
async def export_presentation_as_pptx_or_pdf(
    id: Annotated[uuid.UUID, Body(description="Presentation ID to export")],
    export_as: Annotated[
        Literal["pptx", "pdf"], Body(description="Format to export the presentation as")
    ] = "pptx",
    sql_session: AsyncSession = Depends(get_async_session),
):
    presentation = await sql_session.get(PresentationModel, id)

    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    presentation_and_path = await export_presentation(
        id,
        presentation.title or str(uuid.uuid4()),
        export_as,
    )

    return PresentationPathAndEditPath(
        **presentation_and_path.model_dump(),
        edit_path=f"/presentation?id={id}",
    )


async def check_if_api_request_is_valid(
    request: GeneratePresentationRequest,
    sql_session: AsyncSession = Depends(get_async_session),
) -> Tuple[uuid.UUID,]:
    presentation_id = uuid.uuid4()
    print(f"Presentation ID: {presentation_id}")

    # Making sure either content, slides markdown or files is provided
    if not (request.content or request.slides_markdown or request.files):
        raise HTTPException(
            status_code=400,
            detail="Either content or slides markdown or files is required to generate presentation",
        )

    # Making sure number of slides is greater than 0
    if request.n_slides <= 0:
        raise HTTPException(
            status_code=400,
            detail="Number of slides must be greater than 0",
        )

    # Checking if template is valid
    if request.template not in DEFAULT_TEMPLATES:
        request.template = request.template.lower()
        if not request.template.startswith("custom-"):
            raise HTTPException(
                status_code=400,
                detail="Template not found. Please use a valid template.",
            )
        template_id = request.template.replace("custom-", "")
        try:
            template = await sql_session.get(TemplateModel, uuid.UUID(template_id))
            if not template:
                raise Exception()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail="Template not found. Please use a valid template.",
            )

    return (presentation_id,)


async def generate_presentation_handler(
    request: GeneratePresentationRequest,
    presentation_id: uuid.UUID,
    async_status: Optional[AsyncPresentationGenerationTaskModel],
    sql_session: AsyncSession = Depends(get_async_session),
):
    try:
        using_slides_markdown = False
        web_context_text: Optional[str] = None

        if request.slides_markdown:
            using_slides_markdown = True
            request.n_slides = len(request.slides_markdown)

        print("[WEB SEARCH DEBUG] Web search is always enabled")
        try:
            print(f"[WEB SEARCH] Fetching outline context for query: {request.content[:100]}")
            web_results = await WEB_SEARCH_SERVICE.search(request.content)
            web_context_text = WEB_SEARCH_SERVICE.results_to_text(web_results)
            print(f"[WEB SEARCH] Outline context built - {len(web_results)} results, preview: {(web_context_text or '')[:200]}")
        except Exception as exc:
            print(f"[WEB SEARCH] Outline search failed: {exc}")

        if not using_slides_markdown:
            additional_context = ""

            # Updating async status
            if async_status:
                async_status.message = "Generating presentation outlines"
                async_status.updated_at = datetime.now()
                sql_session.add(async_status)
                await sql_session.commit()

            if request.files:
                documents_loader = DocumentsLoader(file_paths=request.files)
                await documents_loader.load_documents()
                documents = documents_loader.documents
                if documents:
                    additional_context = "\n\n".join(documents)

            if web_context_text:
                additional_context = "\n\n".join(
                    [
                        part
                        for part in [additional_context, f"Web search findings:\n{web_context_text}"]
                        if part and part.strip()
                    ]
                )

            # Finding number of slides to generate by considering table of contents
            n_slides_to_generate = request.n_slides
            if request.include_table_of_contents:
                needed_toc_count = math.ceil(
                    (
                        (request.n_slides - 1)
                        if request.include_title_slide
                        else request.n_slides
                    )
                    / 10
                )
                n_slides_to_generate -= math.ceil(
                    (request.n_slides - needed_toc_count) / 10
                )

            presentation_outlines_text = ""
            async for chunk in generate_ppt_outline(
                request.content,
                n_slides_to_generate,
                request.language,
                additional_context,
                request.tone.value,
                request.verbosity.value,
                request.instructions,
                request.include_title_slide,
            ):

                if isinstance(chunk, HTTPException):
                    raise chunk

                presentation_outlines_text += chunk

            try:
                presentation_outlines_json = dict(
                    dirtyjson.loads(presentation_outlines_text)
                )
            except Exception as e:
                traceback.print_exc()
                raise HTTPException(
                    status_code=400,
                    detail="Failed to generate presentation outlines. Please try again.",
                )
            presentation_outlines = PresentationOutlineModel(
                **presentation_outlines_json
            )
            total_outlines = n_slides_to_generate

        else:
            # Setting outlines to slides markdown
            presentation_outlines = PresentationOutlineModel(
                slides=[
                    SlideOutlineModel(content=slide)
                    for slide in request.slides_markdown
                ]
            )
            total_outlines = len(request.slides_markdown)

        # Updating async status
        if async_status:
            async_status.message = f"Selecting layout for each slide"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        print("-" * 40)
        print(f"Generated {total_outlines} outlines for the presentation")

        # Parse Layouts
        layout_model = await get_layout_by_name(request.template)
        total_slide_layouts = len(layout_model.slides)

        # Generate Structure
        if layout_model.ordered:
            presentation_structure = layout_model.to_presentation_structure()
        else:
            presentation_structure: PresentationStructureModel = (
                await generate_presentation_structure(
                    presentation_outlines,
                    layout_model,
                    request.instructions,
                    using_slides_markdown,
                    query=request.content or request.topic,
                )
            )

        presentation_structure.slides = presentation_structure.slides[:total_outlines]
        for index in range(total_outlines):
            random_slide_index = random.randint(0, total_slide_layouts - 1)
            if index >= total_outlines:
                presentation_structure.slides.append(random_slide_index)
                continue
            if presentation_structure.slides[index] >= total_slide_layouts:
                presentation_structure.slides[index] = random_slide_index

        # Injecting table of contents to the presentation structure and outlines
        if request.include_table_of_contents and not using_slides_markdown:
            n_toc_slides = request.n_slides - total_outlines
            toc_slide_layout_index = select_toc_or_list_slide_layout_index(layout_model)
            if toc_slide_layout_index != -1:
                outline_index = 1 if request.include_title_slide else 0
                for i in range(n_toc_slides):
                    outlines_to = outline_index + 10
                    if total_outlines == outlines_to:
                        outlines_to -= 1

                    presentation_structure.slides.insert(
                        i + 1 if request.include_title_slide else i,
                        toc_slide_layout_index,
                    )
                    toc_outline = f"Table of Contents\n\n"

                    for outline in presentation_outlines.slides[
                        outline_index:outlines_to
                    ]:
                        page_number = (
                            outline_index - i + n_toc_slides + 1
                            if request.include_title_slide
                            else outline_index - i + n_toc_slides
                        )
                        toc_outline += f"Slide page number: {page_number}\n Slide Content: {outline.content[:100]}\n\n"
                        outline_index += 1

                    outline_index += 1

                    presentation_outlines.slides.insert(
                        i + 1 if request.include_title_slide else i,
                        SlideOutlineModel(
                            content=toc_outline,
                        ),
                    )

        # Create PresentationModel
        presentation = PresentationModel(
            id=presentation_id,
            content=request.content,
            n_slides=request.n_slides,
            language=request.language,
            title=get_presentation_title_from_outlines(presentation_outlines),
            outlines=presentation_outlines.model_dump(),
            layout=layout_model.model_dump(),
            structure=presentation_structure.model_dump(),
            tone=request.tone.value,
            verbosity=request.verbosity.value,
            instructions=request.instructions,
            web_search=True,
        )

        # Updating async status
        if async_status:
            async_status.message = "Generating slides"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        image_generation_service = ImageGenerationService(get_images_directory())
        async_assets_generation_tasks = []

        # 7. Generate slide content concurrently (batched), then build slides and fetch assets
        slides: List[SlideModel] = []

        slide_layout_indices = presentation_structure.slides
        slide_layouts = [layout_model.slides[idx] for idx in slide_layout_indices]

        if web_context_text:
            print(f"[WEB SEARCH] Passing context into slide generation - {len(web_context_text)} chars, preview: {web_context_text[:200]}")

        # Schedule slide content generation and asset fetching in batches of 10
        batch_size = 10
        for start in range(0, len(slide_layouts), batch_size):
            end = min(start + batch_size, len(slide_layouts))

            print(f"Generating slides from {start} to {end}")

            # Generate contents for this batch concurrently
            content_tasks = [
                get_slide_content_from_type_and_outline(
                    slide_layouts[i],
                    presentation_outlines.slides[i],
                    request.language,
                    request.tone.value,
                    request.verbosity.value,
                    request.instructions,
                    web_context_text,
                )
                for i in range(start, end)
            ]
            batch_contents: List[dict] = await asyncio.gather(*content_tasks)

            # Build slides for this batch
            batch_slides: List[SlideModel] = []
            for offset, slide_content in enumerate(batch_contents):
                i = start + offset
                slide_layout = slide_layouts[i]
                slide = SlideModel(
                    presentation=presentation_id,
                    layout_group=layout_model.name,
                    layout=slide_layout.id,
                    index=i,
                    speaker_note=slide_content.get("__speaker_note__"),
                    content=slide_content,
                )
                slides.append(slide)
                batch_slides.append(slide)

            # Start asset fetch tasks for just-generated slides so they run while next batch is processed
            asset_tasks = [
                process_slide_and_fetch_assets(image_generation_service, slide)
                for slide in batch_slides
            ]
            async_assets_generation_tasks.extend(asset_tasks)

        if async_status:
            async_status.message = "Fetching assets for slides"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        # Run all asset tasks concurrently while batches may still be generating content
        generated_assets_list = await asyncio.gather(*async_assets_generation_tasks)
        generated_assets = []
        for assets_list in generated_assets_list:
            generated_assets.extend(assets_list)

        # 8. Save PresentationModel and Slides
        sql_session.add(presentation)
        sql_session.add_all(slides)
        sql_session.add_all(generated_assets)
        await sql_session.commit()

        if async_status:
            async_status.message = "Exporting presentation"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)

        # 9. Export
        presentation_and_path = await export_presentation(
            presentation_id, presentation.title or str(uuid.uuid4()), request.export_as
        )

        response = PresentationPathAndEditPath(
            **presentation_and_path.model_dump(),
            edit_path=f"/presentation?id={presentation_id}",
        )

        if async_status:
            async_status.message = "Presentation generation completed"
            async_status.status = "completed"
            async_status.data = response.model_dump(mode="json")
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        # Triggering webhook on success
        CONCURRENT_SERVICE.run_task(
            None,
            WebhookService.send_webhook,
            WebhookEvent.PRESENTATION_GENERATION_COMPLETED,
            response.model_dump(mode="json"),
        )

        return response

    except Exception as e:
        if not isinstance(e, HTTPException):
            traceback.print_exc()
            e = HTTPException(status_code=500, detail="Presentation generation failed")

        api_error_model = APIErrorModel.from_exception(e)

        # Triggering webhook on failure
        CONCURRENT_SERVICE.run_task(
            None,
            WebhookService.send_webhook,
            WebhookEvent.PRESENTATION_GENERATION_FAILED,
            api_error_model.model_dump(mode="json"),
        )

        if async_status:
            async_status.status = "error"
            async_status.message = "Presentation generation failed"
            async_status.updated_at = datetime.now()
            async_status.error = api_error_model.model_dump(mode="json")
            sql_session.add(async_status)
            await sql_session.commit()

        else:
            raise e


@PRESENTATION_ROUTER.post("/generate", response_model=PresentationPathAndEditPath)
async def generate_presentation_sync(
    request: GeneratePresentationRequest,
    sql_session: AsyncSession = Depends(get_async_session),
):
    try:
        (presentation_id,) = await check_if_api_request_is_valid(request, sql_session)
        return await generate_presentation_handler(
            request, presentation_id, None, sql_session
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Presentation generation failed")


@PRESENTATION_ROUTER.post(
    "/generate/async", response_model=AsyncPresentationGenerationTaskModel
)
async def generate_presentation_async(
    request: GeneratePresentationRequest,
    background_tasks: BackgroundTasks,
    sql_session: AsyncSession = Depends(get_async_session),
):
    try:
        (presentation_id,) = await check_if_api_request_is_valid(request, sql_session)

        async_status = AsyncPresentationGenerationTaskModel(
            status="pending",
            message="Queued for generation",
            data=None,
        )
        sql_session.add(async_status)
        await sql_session.commit()

        background_tasks.add_task(
            generate_presentation_handler,
            request,
            presentation_id,
            async_status=async_status,
            sql_session=sql_session,
        )
        return async_status

    except Exception as e:
        if not isinstance(e, HTTPException):
            print(e)
            e = HTTPException(status_code=500, detail="Presentation generation failed")

        raise e


@PRESENTATION_ROUTER.get(
    "/status/{id}", response_model=AsyncPresentationGenerationTaskModel
)
async def check_async_presentation_generation_status(
    id: str = Path(description="ID of the presentation generation task"),
    sql_session: AsyncSession = Depends(get_async_session),
):
    status = await sql_session.get(AsyncPresentationGenerationTaskModel, id)
    if not status:
        raise HTTPException(
            status_code=404, detail="No presentation generation task found"
        )
    return status


@PRESENTATION_ROUTER.post("/edit", response_model=PresentationPathAndEditPath)
async def edit_presentation_with_new_content(
    data: Annotated[EditPresentationRequest, Body()],
    sql_session: AsyncSession = Depends(get_async_session),
):
    presentation = await sql_session.get(PresentationModel, data.presentation_id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    slides = await sql_session.scalars(
        select(SlideModel).where(SlideModel.presentation == data.presentation_id)
    )

    new_slides = []
    slides_to_delete = []
    for each_slide in slides:
        updated_content = None
        new_slide_data = list(
            filter(lambda x: x.index == each_slide.index, data.slides)
        )
        if new_slide_data:
            updated_content = deep_update(each_slide.content, new_slide_data[0].content)
            new_slides.append(
                each_slide.get_new_slide(presentation.id, updated_content)
            )
            slides_to_delete.append(each_slide.id)

    await sql_session.execute(
        delete(SlideModel).where(SlideModel.id.in_(slides_to_delete))
    )

    sql_session.add_all(new_slides)
    await sql_session.commit()

    presentation_and_path = await export_presentation(
        presentation.id, presentation.title or str(uuid.uuid4()), data.export_as
    )

    return PresentationPathAndEditPath(
        **presentation_and_path.model_dump(),
        edit_path=f"/presentation?id={presentation.id}",
    )


@PRESENTATION_ROUTER.post("/derive", response_model=PresentationPathAndEditPath)
async def derive_presentation_from_existing_one(
    data: Annotated[EditPresentationRequest, Body()],
    sql_session: AsyncSession = Depends(get_async_session),
):
    presentation = await sql_session.get(PresentationModel, data.presentation_id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    slides = await sql_session.scalars(
        select(SlideModel).where(SlideModel.presentation == data.presentation_id)
    )

    new_presentation = presentation.get_new_presentation()
    new_slides = []
    for each_slide in slides:
        updated_content = None
        new_slide_data = list(
            filter(lambda x: x.index == each_slide.index, data.slides)
        )
        if new_slide_data:
            updated_content = deep_update(each_slide.content, new_slide_data[0].content)
        new_slides.append(
            each_slide.get_new_slide(new_presentation.id, updated_content)
        )

    sql_session.add(new_presentation)
    sql_session.add_all(new_slides)
    await sql_session.commit()

    presentation_and_path = await export_presentation(
        new_presentation.id, new_presentation.title or str(uuid.uuid4()), data.export_as
    )

    return PresentationPathAndEditPath(
        **presentation_and_path.model_dump(),
        edit_path=f"/presentation?id={new_presentation.id}",
    )


class VideoInfo(BaseModel):
    """Information about a generated video"""
    video_id: uuid.UUID
    slide_index: int
    prompt: str
    video_url: str
    created_at: datetime
    completed_at: Optional[datetime]


@PRESENTATION_ROUTER.get("/{presentation_id}/videos", response_model=List[VideoInfo])
async def get_presentation_videos(
    presentation_id: Annotated[uuid.UUID, Path(description="Presentation ID")],
    sql_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> List[VideoInfo]:
    """
    Get all successfully generated videos for a presentation.
    Returns video metadata including download URLs.
    """
    from models.sql.video_job import VideoJob, VideoJobStatus
    from models.sql.video_asset import VideoAsset
    import os
    from utils.get_env import get_app_data_directory_env
    
    app_data_dir = get_app_data_directory_env()
    
    # Query all EMBEDDED video jobs for this presentation
    stmt = (
        select(VideoJob, VideoAsset)
        .join(VideoAsset, VideoJob.video_asset_id == VideoAsset.id, isouter=False)
        .where(VideoJob.presentation_id == presentation_id)
        .where(VideoJob.status == VideoJobStatus.EMBEDDED)
        .order_by(VideoJob.slide_index)
    )
    
    results = await sql_session.execute(stmt)
    rows = results.all()
    
    videos = []
    for job, asset in rows:
        # Build video URL using same logic as embedding phase
        if asset and asset.path:
            if asset.path.startswith(app_data_dir):
                relative_path = os.path.relpath(asset.path, app_data_dir)
                relative_path = relative_path.replace(os.sep, "/")
                video_url = f"/app_data/{relative_path}"
            else:
                video_url = asset.path
        else:
            video_url = None
            
        videos.append(
            VideoInfo(
                video_id=job.id,
                slide_index=job.slide_index,
                prompt=job.prompt,
                video_url=video_url,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )
        )
    
    return videos
