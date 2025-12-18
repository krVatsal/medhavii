import asyncio
import os
import sys

# Add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from services.manim_service import ManimService

load_dotenv()

async def test_manim():
    print("Testing Manim Service...")
    service = ManimService()
    
    # Complex prompt similar to what the presentation generates
    prompt = "Animate a 2D vector being rotated by 45 degrees using a rotation matrix. Show the original vector, the rotation matrix application, and the resulting vector."
    
    print(f"Prompt: {prompt}")
    result = await service.generate_video(prompt)
    
    if result:
        print(f"Success! Video generated at: {result.path}")
        print(f"URL: {result.extras.get('url')}")
    else:
        print("Failed to generate video.")

if __name__ == "__main__":
    # Fix for Windows asyncio loop policy if needed, though usually handled by uvicorn
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(test_manim())
