from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.image_prompt import ImagePrompt
from models.sql.image_asset import ImageAsset
from services.database import get_async_session
from services.image_generation_service import ImageGenerationService
from utils.asset_directory_utils import get_images_directory
from utils.get_env import get_app_data_directory_env
from middlewares.auth_middleware import require_auth
import os
import uuid
from utils.file_utils import get_file_name_with_random_uuid

IMAGES_ROUTER = APIRouter(prefix="/images", tags=["Images"])


def get_image_url(image_id: uuid.UUID) -> str:
    """Generate URL for accessing image from database"""
    return f"/api/v1/ppt/images/{image_id}/data"


@IMAGES_ROUTER.get("/generate")
async def generate_image(
    prompt: str,
    user_id: uuid.UUID = Depends(require_auth),
    sql_session: AsyncSession = Depends(get_async_session)
):
    images_directory = get_images_directory()
    image_prompt = ImagePrompt(prompt=prompt)
    image_generation_service = ImageGenerationService(images_directory)

    image = await image_generation_service.generate_image(image_prompt)
    if not isinstance(image, ImageAsset):
        return image

    # Link image to user
    image.user_id = user_id

    # Read the file and store binary data
    if image.path and os.path.exists(image.path):
        with open(image.path, "rb") as f:
            image.binary_data = f.read()
            image.file_size = len(image.binary_data)
            image.filename = os.path.basename(image.path)
        # Remove local file after storing in DB
        try:
            os.remove(image.path)
        except Exception as e:
            print(f"Warning: Could not remove temporary file {image.path}: {e}")

    sql_session.add(image)
    await sql_session.commit()

    return get_image_url(image.id)


@IMAGES_ROUTER.get("/generated", response_model=List[ImageAsset])
async def get_generated_images(
    user_id: uuid.UUID = Depends(require_auth),
    sql_session: AsyncSession = Depends(get_async_session)
):
    try:
        images = await sql_session.scalars(
            select(ImageAsset)
            .where(ImageAsset.is_uploaded == False)
            .where(ImageAsset.user_id == user_id)
            .order_by(ImageAsset.created_at.desc())
        )
        images_list = images.all()
        # Replace path with URL to fetch binary data
        for img in images_list:
            img.path = get_image_url(img.id)
            # Don't send binary data in list responses to reduce payload
            img.binary_data = None
        return images_list
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve generated images: {str(e)}"
        )


@IMAGES_ROUTER.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(require_auth),
    sql_session: AsyncSession = Depends(get_async_session)
):
    try:
        # Read file content
        file_content = await file.read()
        
        # Determine content type
        content_type = file.content_type or "image/png"
        
        # Create image asset with binary data
        image_asset = ImageAsset(
            binary_data=file_content,
            filename=file.filename,
            content_type=content_type,
            file_size=len(file_content),
            is_uploaded=True,
            user_id=user_id
        )

        sql_session.add(image_asset)
        await sql_session.commit()
        
        # Return with URL for fetching
        image_asset.path = get_image_url(image_asset.id)
        image_asset.binary_data = None  # Don't send binary in response

        return image_asset
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


@IMAGES_ROUTER.get("/uploaded", response_model=List[ImageAsset])
async def get_uploaded_images(
    user_id: uuid.UUID = Depends(require_auth),
    sql_session: AsyncSession = Depends(get_async_session)
):
    try:
        images = await sql_session.scalars(
            select(ImageAsset)
            .where(ImageAsset.is_uploaded == True)
            .where(ImageAsset.user_id == user_id)
            .order_by(ImageAsset.created_at.desc())
        )
        images_list = images.all()
        # Replace path with URL to fetch binary data
        for img in images_list:
            img.path = get_image_url(img.id)
            # Don't send binary data in list responses
            img.binary_data = None
        return images_list
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve uploaded images: {str(e)}"
        )


@IMAGES_ROUTER.delete("/{id}", status_code=204)
async def delete_uploaded_image_by_id(
    id: uuid.UUID, sql_session: AsyncSession = Depends(get_async_session)
):
    try:
        # Fetch the asset
        image = await sql_session.get(ImageAsset, id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

        # Remove local file if it exists (for backward compatibility)
        if image.path and os.path.exists(image.path):
            try:
                os.remove(image.path)
            except Exception as e:
                print(f"Warning: Could not remove file {image.path}: {e}")

        await sql_session.delete(image)
        await sql_session.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")


@IMAGES_ROUTER.get("/{id}/data")
async def get_image_data(
    id: uuid.UUID, sql_session: AsyncSession = Depends(get_async_session)
):
    """Serve image binary data from database"""
    try:
        image = await sql_session.get(ImageAsset, id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        if not image.binary_data:
            # Fallback to file if binary data not available (backward compatibility)
            if image.path and os.path.exists(image.path):
                with open(image.path, "rb") as f:
                    binary_data = f.read()
                content_type = image.content_type or "image/png"
                return Response(content=binary_data, media_type=content_type)
            raise HTTPException(status_code=404, detail="Image data not found")
        
        content_type = image.content_type or "image/png"
        return Response(content=image.binary_data, media_type=content_type)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")
