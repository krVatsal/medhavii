import asyncio
import os
import aiohttp
from google import genai
from google.genai.types import GenerateContentConfig
from openai import AsyncOpenAI
from models.image_prompt import ImagePrompt
from models.sql.image_asset import ImageAsset
from utils.download_helpers import download_file
from utils.get_env import get_pexels_api_key_env
from utils.get_env import get_pixabay_api_key_env
from utils.image_provider import (
    is_pixels_selected,
    is_pixabay_selected,
    is_gemini_flash_selected,
    is_dalle3_selected,
)
import uuid


class ImageGenerationService:

    def __init__(self, output_directory: str):
        self.output_directory = output_directory
        self.image_gen_func = self.get_image_gen_func()

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
        """
        Generates an image based on the provided prompt.
        - If no image generation function is available, returns a placeholder image.
        - If stock providers are available, tries them with fallbacks (Pexels -> Pixabay).
        - For AI providers, uses the configured provider.
        - Output Directory is used for saving AI-generated images, not stock providers.
        """
        if not self.image_gen_func:
            print("No image generation function found. Using placeholder image.")
            return "/static/images/placeholder.jpg"

        image_prompt = prompt.get_image_prompt(
            with_theme=not self.is_stock_provider_selected()
        )
        print(f"Request - Generating Image for {image_prompt}")

        # For stock providers, try multiple sources with fallback
        if self.is_stock_provider_selected():
            # Try Pexels first
            if get_pexels_api_key_env():
                try:
                    print("Trying Pexels...")
                    image_path = await self.get_image_from_pexels(image_prompt)
                    if image_path:
                        return image_path
                except Exception as e:
                    print(f"Pexels failed: {e}")
            
            # Fallback to Pixabay
            if get_pixabay_api_key_env():
                try:
                    print("Trying Pixabay as fallback...")
                    image_path = await self.get_image_from_pixabay(image_prompt)
                    if image_path:
                        return image_path
                except Exception as e:
                    print(f"Pixabay failed: {e}")
            
            print("All stock providers failed. Using placeholder.")
            return "/static/images/placeholder.jpg"
        
        # For AI providers, use the configured one
        try:
            image_path = await self.image_gen_func(
                image_prompt, self.output_directory
            )
            if image_path:
                if image_path.startswith("http"):
                    return image_path
                elif os.path.exists(image_path):
                    return ImageAsset(
                        path=image_path,
                        is_uploaded=False,
                        extras={
                            "prompt": prompt.prompt,
                            "theme_prompt": prompt.theme_prompt,
                        },
                    )
            raise Exception(f"Image not found at {image_path}")

        except Exception as e:
            print(f"Error generating image: {e}")
            return "/static/images/placeholder.jpg"

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
        client = genai.Client()
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash-image-preview",
            contents=[prompt],
            config=GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )

        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                image_path = os.path.join(output_directory, f"{uuid.uuid4()}.jpg")
                with open(image_path, "wb") as f:
                    f.write(part.inline_data.data)

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
            data = await response.json()
            
            if response.status != 200:
                raise Exception(f"Pexels API error: {data.get('error', 'Unknown error')}")
            
            if not data.get("photos") or len(data["photos"]) == 0:
                raise Exception(f"No images found for query: {prompt}")
            
            image_url = data["photos"][0]["src"]["large"]
            return image_url

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
            return image_url
