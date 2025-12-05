import asyncio
from dotenv import load_dotenv  # ← Add this
from services.image_generation_service import ImageGenerationService
from models.image_prompt import ImagePrompt

# Load environment variables from .env file
load_dotenv()  # ← Add this

async def test():
    service = ImageGenerationService(output_directory="tmp/images")
    result = await service.generate_image(
        ImagePrompt(prompt="mountain sunset", theme_prompt="minimalist")
    )
    print(f"Final result: {result}")

if __name__ == "__main__":
    asyncio.run(test())