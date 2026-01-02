import asyncio
import os
import aiohttp
from google import genai # type: ignore
from google.genai.types import GenerateContentConfig # type: ignore
from openai import AsyncOpenAI # type: ignore
from models.image_prompt import ImagePrompt
from models.sql.image_asset import ImageAsset
from utils.download_helpers import download_file # type: ignore
from utils.get_env import get_pexels_api_key_env
from utils.get_env import get_pixabay_api_key_env
from utils.image_provider import (
    is_pixels_selected,
    is_pixabay_selected,
    is_gemini_flash_selected,
    is_dalle3_selected,
)
import uuid
from services.image_scoring import score_image
from datetime import datetime
from sqlmodel import Session, select
from services.database import sql_engine

# Tuning constants
SCORE_THRESHOLD = 0.65  # Raised from 0.50 to filter out irrelevant stock images
MAX_IMAGE_ATTEMPTS = 3


class ImageGenerationService:

    def __init__(self, output_directory: str, user_id: uuid.UUID | None = None):
        self.output_directory = output_directory
        self.user_id = user_id
        self.image_gen_func = self.get_image_gen_func()

    async def save_image_to_db(self, file_path: str, prompt: str, user_id: uuid.UUID | None = None) -> ImageAsset:
        """Save image file to database and optionally delete local file"""
        from services.database import get_async_session
        
        # Read the file content
        with open(file_path, 'rb') as f:
            binary_data = f.read()
        
        # Get file metadata
        filename = os.path.basename(file_path)
        content_type = 'image/jpeg'  # Default, could be detected from file extension
        file_size = len(binary_data)
        
        # Create database record
        image_asset = ImageAsset(
            path=None,  # No path since stored in DB
            is_uploaded=False,
            created_at=datetime.now(),
            binary_data=binary_data,
            user_id=user_id or self.user_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            extras={"prompt": prompt}
        )
        
        # Save to database using async session
        async_gen = get_async_session()
        session = await async_gen.__anext__()
        try:
            session.add(image_asset)
            await session.commit()
            await session.refresh(image_asset)
        finally:
            await async_gen.aclose()
        
        # Delete local file after successful DB save
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[DB SAVE] ✓ Deleted local file: {file_path}")
        except Exception as e:
            print(f"[DB SAVE] ⚠️ Could not delete local file: {e}")
        
        print(f"[DB SAVE] ✓ Saved to database with ID: {image_asset.id}")
        return image_asset

    def get_image_gen_func(self):
        if is_pixabay_selected():
            return self.get_image_from_pixabay
        elif is_pixels_selected():
            return self.get_image_from_pexels
        elif is_gemini_flash_selected():
            return self.generate_image_google
        elif is_dalle3_selected():
            return self.generate_image_openai
        return None

    def is_stock_provider_selected(self):
        return is_pixels_selected() or is_pixabay_selected()

    async def generate_image(self, prompt: ImagePrompt) -> str | ImageAsset:
        if not self.image_gen_func:
            print("No image generation function found. Using placeholder image.")
            return "/static/images/placeholder.jpg"

        image_prompt = prompt.get_image_prompt(
            with_theme=not self.is_stock_provider_selected()
        )
        print(f"Request - Generating Image for {image_prompt}")

        attempts = 0
        last_error = None
        
        while attempts < MAX_IMAGE_ATTEMPTS:
            attempts += 1
            try:
                candidate = await self._fetch_image_candidate(image_prompt, prompt)
                
                if not candidate:
                    last_error = "No candidate returned"
                    print(f"Attempt {attempts}: No candidate. Retrying...")
                    await asyncio.sleep(0.5)
                    continue
                
                clip_prompt = prompt.get_image_prompt(with_theme=True)
                
                # For scoring, we need the binary data from the DB
                if isinstance(candidate, ImageAsset):
                    # Create a temp file for scoring
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                        tmp.write(candidate.binary_data)
                        tmp_path = tmp.name
                    
                    try:
                        score = await score_image(tmp_path, prompt=clip_prompt)
                        print(f"Attempt {attempts}: score={score:.3f} (threshold={SCORE_THRESHOLD})")
                        
                        if score >= SCORE_THRESHOLD:
                            print(f"✓ Image accepted (score={score:.3f})")
                            return candidate
                        else:
                            print(f"✗ Image rejected (score={score:.3f}), retrying...")
                            # Delete from database if rejected
                            with Session(sql_engine) as session:
                                session.delete(candidate)
                                session.commit()
                    finally:
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                else:
                    # String path case (shouldn't happen now, but keep for safety)
                    score = await score_image(candidate, prompt=clip_prompt)
                    if score >= SCORE_THRESHOLD:
                        return candidate
                    
            except Exception as e:
                last_error = str(e)
                print(f"Attempt {attempts} error: {e}")
                await asyncio.sleep(0.5)
        
        print(f"Exhausted {MAX_IMAGE_ATTEMPTS} attempts. Last error: {last_error}")
        return "/static/images/placeholder.jpg"
    
    async def _fetch_image_candidate(self, image_prompt: str, original_prompt: ImagePrompt) -> str | ImageAsset | None:
        if self.is_stock_provider_selected():
            print("[FETCH] Using stock image provider")
        
            if get_pexels_api_key_env():
                try:
                    print("[FETCH] Trying Pexels API...")
                    local_path = await self.get_image_from_pexels(image_prompt)
                    if local_path and os.path.exists(local_path):
                        print(f"[FETCH] ✓ Pexels success")
                        # Save to database and delete local file
                        image_asset = await self.save_image_to_db(
                            local_path,
                            prompt=original_prompt.prompt,
                            user_id=self.user_id
                        )
                        return image_asset
                except Exception as e:
                    print(f"[FETCH] ✗ Pexels failed: {e}")
        
            if get_pixabay_api_key_env():
                try:
                    print("[FETCH] Trying Pixabay API...")
                    local_path = await self.get_image_from_pixabay(image_prompt)
                    if local_path and os.path.exists(local_path):
                        print(f"[FETCH] ✓ Pixabay success")
                        # Save to database and delete local file
                        image_asset = await self.save_image_to_db(
                            local_path,
                            prompt=original_prompt.prompt,
                            user_id=self.user_id
                        )
                        return image_asset
                except Exception as e:
                    print(f"[FETCH] ✗ Pixabay failed: {e}")
        
            print("[FETCH] ✗ All stock providers failed")
            return None
        
        print("[FETCH] Using AI image generation")
        
        if not self.image_gen_func:
            print("[FETCH] ✗ No AI function available")
            return None
        
        try:
            image_path = await self.image_gen_func(image_prompt, self.output_directory)
            
            if not image_path:
                print("[FETCH] ✗ AI returned no path")
                return None
            
            if not isinstance(image_path, str):
                print(f"[FETCH] ✗ Invalid path type")
                return None
            
            if os.path.exists(image_path):
                print(f"[FETCH] ✓ AI image generated")
                # Save to database and delete local file
                image_asset = await self.save_image_to_db(
                    image_path,
                    prompt=original_prompt.prompt,
                    user_id=self.user_id
                )
                return image_asset
            else:
                print(f"[FETCH] ✗ AI path doesn't exist")
                return None

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"[FETCH] ⚠️ Google API quota exhausted - skipping image")
            else:
                print(f"[FETCH] ⚠️ AI error: {error_msg[:100]}")
            return None

    async def generate_image_openai(self, prompt: str, output_directory: str) -> str:
        client = AsyncOpenAI()
        result = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            quality="standard",
            size="1024x1024",
        )
        image_url = result.data[0].url
        return await download_file(image_url, output_directory)

    async def generate_image_google(self, prompt: str, output_directory: str) -> str:
        client = genai.Client()  # type: ignore
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash-image-preview",
            contents=[prompt],
            config=GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        
        image_path = None
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                image_path = os.path.join(output_directory, f"{uuid.uuid4()}.jpg")
                with open(image_path, "wb") as f:
                    f.write(part.inline_data.data)
                break  # ← Stop after first image

        if not image_path:  # ← Fixed: handle no image case
            raise Exception("No image data returned from Gemini")
        
        return image_path

    async def get_image_from_pexels(self, prompt: str) -> str:
        api_key = get_pexels_api_key_env()
        if not api_key:
            raise Exception("PEXELS_API_KEY not configured")
        
        async with aiohttp.ClientSession(trust_env=True) as session:
            response = await session.get(
                f"https://api.pexels.com/v1/search?query={prompt}&per_page=1",
                headers={"Authorization": api_key},
            )
            
            if response.status != 200:
                error_text = await response.text()
                print(f"[PEXELS ERROR] Status: {response.status}")
                print(f"[PEXELS ERROR] Response: {error_text}")
                raise Exception(f"Pexels API error (Status {response.status}): {error_text}")
            
            data = await response.json()
            
            if not data.get("photos") or len(data["photos"]) == 0:
                raise Exception(f"No images found for query: {prompt}")
            
            image_url = data["photos"][0]["src"]["large"]
            print(f"[DEBUG] Pexels URL: {image_url}")
            
            # Download to local file for PPT insertion
            local_path = await download_file(image_url, self.output_directory)
            print(f"[DEBUG] Downloaded to: {local_path}")
            print(f"[DEBUG] File exists? {os.path.exists(local_path)}")
            print(f"[DEBUG] File size: {os.path.getsize(local_path) if os.path.exists(local_path) else 'N/A'} bytes")
        
        return local_path

    async def get_image_from_pixabay(self, prompt: str) -> str:
        api_key = get_pixabay_api_key_env()
        if not api_key:
            raise Exception("PIXABAY_API_KEY not configured")
        
        async with aiohttp.ClientSession(trust_env=True) as session:
            response = await session.get(
                f"https://pixabay.com/api/?key={api_key}&q={prompt}&image_type=photo&per_page=3"
            )
            data = await response.json()
            
            if response.status != 200:
                raise Exception(f"Pixabay API error: {data.get('message', 'Unknown error')}")
            
            if not data.get("hits") or len(data["hits"]) == 0:
                raise Exception(f"No images found for query: {prompt}")
            
            image_url = data["hits"][0]["largeImageURL"]
            # Download to local file for PPT insertion
            print(f"Downloading from Pixabay: {image_url}")
            local_path = await download_file(image_url, self.output_directory)
            print(f"Saved to: {local_path}")
            return local_path
