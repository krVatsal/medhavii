"""
Manim Worker - Processes video generation tasks from Redis queue
"""
import asyncio
import json
import os
import sys
from typing import Optional

import redis.asyncio as redis
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.manim_service import ManimService

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QUEUE_NAME = "manim:video:queue"
RESULT_PREFIX = "manim:video:result:"

class ManimWorker:
    def __init__(self):
        self.redis_client = None
        self.manim_service = ManimService()
        
    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        print(f"[MANIM WORKER] Connected to Redis at {REDIS_URL}")
        
    async def process_task(self, task_data: dict) -> dict:
        """Process a video generation task"""
        task_id = task_data.get("task_id")
        prompt = task_data.get("prompt")
        user_id = task_data.get("user_id")
        
        print(f"[MANIM WORKER] Processing task {task_id}: {prompt[:50]}...")
        
        try:
            # Generate video using Manim service
            video_asset = await self.manim_service.generate_video(prompt)
            
            if video_asset:
                result = {
                    "status": "success",
                    "task_id": task_id,
                    "video_id": str(video_asset.id),
                    "url": f"/api/v1/ppt/videos/{video_asset.id}/data"
                }
                print(f"[MANIM WORKER] ✓ Task {task_id} completed: video {video_asset.id}")
            else:
                result = {
                    "status": "error",
                    "task_id": task_id,
                    "error": "Video generation failed"
                }
                print(f"[MANIM WORKER] ✗ Task {task_id} failed")
                
        except Exception as e:
            result = {
                "status": "error",
                "task_id": task_id,
                "error": str(e)
            }
            print(f"[MANIM WORKER] ✗ Task {task_id} error: {e}")
            
        return result
        
    async def run(self):
        """Main worker loop"""
        await self.connect()
        
        print("[MANIM WORKER] Started. Waiting for tasks...")
        
        while True:
            try:
                # Blocking pop from queue (timeout 5s)
                result = await self.redis_client.blpop(QUEUE_NAME, timeout=5)
                
                if result:
                    queue_name, task_json = result
                    task_data = json.loads(task_json)
                    
                    # Process task
                    result = await self.process_task(task_data)
                    
                    # Store result
                    task_id = task_data.get("task_id")
                    result_key = f"{RESULT_PREFIX}{task_id}"
                    await self.redis_client.setex(
                        result_key,
                        3600,  # Expire after 1 hour
                        json.dumps(result)
                    )
                    
            except Exception as e:
                print(f"[MANIM WORKER] Error in main loop: {e}")
                await asyncio.sleep(1)
                
    async def shutdown(self):
        """Cleanup on shutdown"""
        if self.redis_client:
            await self.redis_client.close()
            print("[MANIM WORKER] Disconnected from Redis")

async def main():
    worker = ManimWorker()
    try:
        await worker.run()
    except KeyboardInterrupt:
        print("\n[MANIM WORKER] Shutting down...")
        await worker.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
