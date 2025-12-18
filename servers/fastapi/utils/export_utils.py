import json
import os
import aiohttp
from typing import Literal
import uuid
from fastapi import HTTPException
from pathvalidate import sanitize_filename

from models.pptx_models import (
    PptxPresentationModel,
    PptxVideoBoxModel,
    PptxPictureBoxModel,
    PptxPictureModel,
    PptxShapeModel,
)
from models.presentation_and_path import PresentationAndPath
from services.pptx_presentation_creator import PptxPresentationCreator
from services.temp_file_service import TEMP_FILE_SERVICE
from utils.asset_directory_utils import get_exports_directory


def _demote_non_videos_to_pictures_data(pptx_model_data: dict) -> dict:
    """Normalize raw PPTX model dict so only real videos stay as videos."""

    def transform_shapes(shapes):
        normalized = []
        for shape in shapes or []:
            if isinstance(shape, dict) and shape.get("shape_type") == "video":
                video_info = shape.get("video") or {}
                video_path = (video_info.get("path") or "").lower()
                if not video_path.endswith(".mp4"):
                    normalized.append(
                        {
                            "shape_type": "picture",
                            "position": shape.get("position"),
                            "margin": shape.get("margin"),
                            "clip": True,
                            "opacity": None,
                            "invert": False,
                            "border_radius": None,
                            "shape": None,
                            "object_fit": None,
                            "picture": {
                                "is_network": video_info.get("is_network", False),
                                "path": video_info.get("path", ""),
                            },
                        }
                    )
                else:
                    normalized.append(shape)
            else:
                normalized.append(shape)
        return normalized

    if "shapes" in pptx_model_data:
        pptx_model_data["shapes"] = transform_shapes(pptx_model_data.get("shapes"))

    slides = pptx_model_data.get("slides") or []
    pptx_model_data["slides"] = []
    for slide in slides:
        if isinstance(slide, dict):
            slide = {**slide, "shapes": transform_shapes(slide.get("shapes"))}
        pptx_model_data["slides"].append(slide)

    return pptx_model_data


def _demote_non_videos_to_pictures(pptx_model: PptxPresentationModel) -> PptxPresentationModel:
    """Convert any video boxes that do not point to .mp4 files into picture boxes.

    The upstream PPTX model generator can emit video shapes even when the
    underlying asset is an image placeholder. That causes PowerPoint to embed
    "videos" from JPEGs/PNGs. We normalize by turning those shapes back into
    pictures unless the path ends with .mp4.
    """

    def transform_shapes(shapes):
        normalized: list[PptxShapeModel] = []
        for shape in shapes or []:
            if isinstance(shape, PptxVideoBoxModel):
                if not shape.video.path.lower().endswith(".mp4"):
                    normalized.append(
                        PptxPictureBoxModel(
                            position=shape.position,
                            margin=shape.margin,
                            clip=True,
                            opacity=None,
                            invert=False,
                            border_radius=None,
                            shape=None,
                            object_fit=None,
                            picture=PptxPictureModel(
                                is_network=shape.video.is_network,
                                path=shape.video.path,
                            ),
                        )
                    )
                else:
                    normalized.append(shape)
            else:
                normalized.append(shape)
        return normalized

    if pptx_model.shapes:
        pptx_model.shapes = transform_shapes(pptx_model.shapes)

    for slide in pptx_model.slides:
        slide.shapes = transform_shapes(slide.shapes)

    return pptx_model


async def export_presentation(
    presentation_id: uuid.UUID, title: str, export_as: Literal["pptx", "pdf"]
) -> PresentationAndPath:
    if export_as == "pptx":

        # Get the converted PPTX model from the Next.js service
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://localhost/api/presentation_to_pptx_model?id={presentation_id}"
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Failed to get PPTX model: {error_text}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to convert presentation to PPTX model",
                    )
                pptx_model_data = await response.json()

            pptx_model_data = _demote_non_videos_to_pictures_data(pptx_model_data)

        # Create PPTX file using the converted model
        pptx_model = PptxPresentationModel(**pptx_model_data)
        pptx_model = _demote_non_videos_to_pictures(pptx_model)
        temp_dir = TEMP_FILE_SERVICE.create_temp_dir()
        pptx_creator = PptxPresentationCreator(pptx_model, temp_dir)
        await pptx_creator.create_ppt()

        export_directory = get_exports_directory()
        pptx_path = os.path.join(
            export_directory,
            f"{sanitize_filename(title or str(uuid.uuid4()))}.pptx",
        )
        pptx_creator.save(pptx_path)

        return PresentationAndPath(
            presentation_id=presentation_id,
            path=pptx_path,
        )
    else:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost/api/export-as-pdf",
                json={
                    "id": str(presentation_id),
                    "title": sanitize_filename(title or str(uuid.uuid4())),
                },
            ) as response:
                response_json = await response.json()

        return PresentationAndPath(
            presentation_id=presentation_id,
            path=response_json["path"],
        )
