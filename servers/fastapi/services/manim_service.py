import asyncio
import json
import os
import time
import uuid
from typing import Optional

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq
from langchain_core.messages import ToolMessage

from models.sql.video_asset import VideoAsset
from utils.asset_directory_utils import get_videos_directory

load_dotenv()

class ManimService:
    def __init__(self):
        # MCP server configuration
        self.servers = {
            "manim-server": {
                "transport": "stdio",
                "command": "python",
                "args": ["/opt/manim-mcp-server/src/manim_server.py"],
                "env": {
                    "MANIM_EXECUTABLE": "/usr/local/bin/manim",
                    "PYTHONUTF8": "1",
                    "PYTHONIOENCODING": "utf-8"
                }
            }
        }
        # Limit concurrent Manim executions to avoid rate limits and resource exhaustion
        self._semaphore = asyncio.Semaphore(1)

    def _find_latest_video_in_output_dir(self, min_mtime: float = 0) -> Optional[str]:
        # Hardcoded path based on user input and server config
        base_dir = "/opt/manim-mcp-server/src/media"
        print(f"[MANIM SERVICE] Scanning for videos in: {base_dir} (newer than {min_mtime})")
        
        if not os.path.exists(base_dir):
            print(f"[MANIM SERVICE] Base output directory not found: {base_dir}")
            return None
            
        latest_file = None
        latest_time = 0
        count = 0
        
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".mp4"):
                    full_path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(full_path)
                        # Only consider files modified AFTER our start time
                        if mtime > min_mtime:
                            count += 1
                            if mtime > latest_time:
                                latest_time = mtime
                                latest_file = full_path
                    except OSError:
                        continue
        
        if latest_file:
            print(f"[MANIM SERVICE] Found {count} new .mp4 files. Latest: {latest_file} (mtime: {latest_time})")
        else:
            print(f"[MANIM SERVICE] No new .mp4 files found (checked candidates against min_mtime={min_mtime}).")
            
        return latest_file

    async def generate_video(self, prompt: str) -> Optional[VideoAsset]:
        print(f"[MANIM SERVICE] Video request queued: {prompt[:80]}...")
        
        async with self._semaphore:
            print(f"[MANIM SERVICE] Semaphore acquired, starting generation")
            await asyncio.sleep(3)
            start_time = time.time()
            
            # Keep client reference in scope for entire execution
            client = None
            try:
                # Initialize MCP client (NOT as context manager per langchain-mcp-adapters docs)
                client = MultiServerMCPClient(self.servers)
                tools = await client.get_tools()
                
                # Create named tool lookup
                named_tools = {}
                for tool in tools:
                    named_tools[tool.name] = tool
                
                print(f"[MANIM SERVICE] Available tools: {list(named_tools.keys())}")
                
                if not named_tools:
                    print("[MANIM SERVICE] No tools found.")
                    return None
                
                # Initialize LLM
                llm = ChatGroq(
                    model="openai/gpt-oss-120b",
                    temperature=0.5,
                    max_retries=5,
                    timeout=60
                )
                llm_with_tools = llm.bind_tools(tools)
                
                # Create detailed prompt for Manim animation generation
                manim_prompt = f"""Using Manim, create a short educational animation that visualizes: {prompt}

Requirements:
- Create a clear, simple visualization that illustrates the concept
- Use appropriate shapes, transformations, and animations
- Keep the animation between 3-6 seconds
- Make it visually appealing and easy to understand
- Use colors and labels where helpful

Generate the Manim code using the execute_manim_code tool."""
                
                response = await llm_with_tools.ainvoke(manim_prompt)
                
                if not getattr(response, "tool_calls", None):
                    print(f"[MANIM SERVICE] LLM Reply (no tool calls): {response.content}")
                    return None
                
                # Execute tool calls - keep client alive during execution
                tool_messages = []
                for tc in response.tool_calls:
                    selected_tool = tc["name"]
                    selected_tool_args = tc.get("args") or {}
                    selected_tool_id = tc["id"]
                    
                    print(f"[MANIM SERVICE] Calling tool {selected_tool}")
                    try:
                        # Give the tool invocation extra time
                        result = await asyncio.wait_for(
                            named_tools[selected_tool].ainvoke(selected_tool_args),
                            timeout=120
                        )
                        tool_messages.append(ToolMessage(
                            tool_call_id=selected_tool_id, 
                            content=json.dumps(result)
                        ))
                        print(f"[MANIM SERVICE] Tool {selected_tool} completed successfully")
                    except Exception as tool_error:
                        print(f"[MANIM SERVICE] Tool {selected_tool} failed: {type(tool_error).__name__}: {tool_error}")
                        # Add error message to tool messages
                        tool_messages.append(ToolMessage(
                            tool_call_id=selected_tool_id,
                            content=json.dumps({"error": str(tool_error)})
                        ))
                
                # Get final response
                final_response = await llm_with_tools.ainvoke([manim_prompt, response, *tool_messages])
                print(f"[MANIM SERVICE] Final response: {final_response.content[:200]}...")
                
            except Exception as e:
                print(f"[MANIM SERVICE] Error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Cleanup client if it has a cleanup method
                if client and hasattr(client, 'cleanup'):
                    try:
                        await client.cleanup()
                    except:
                        pass
            
            # Find generated video
            print("[MANIM SERVICE] Searching for generated video...")
            video_path = self._find_latest_video_in_output_dir(min_mtime=start_time - 5)

            if video_path and os.path.exists(video_path):
                print(f"[MANIM SERVICE] Found video: {video_path}")
                
                # Copy to temp location first
                filename = f"{uuid.uuid4()}.mp4"
                dest_path = os.path.join(get_videos_directory(), filename)
                import shutil
                shutil.copy2(video_path, dest_path)
                print(f"[MANIM SERVICE] Video copied to: {dest_path}")
                
                # Save to database and delete local file
                video_asset = await self._save_video_to_db(dest_path, prompt)
                
                return video_asset
            else:
                print("[MANIM SERVICE] No video found.")
                return None
    
    async def _save_video_to_db(self, file_path: str, prompt: str, user_id=None) -> VideoAsset:
        """Save video file to database and delete local file"""
        from services.database import get_async_session
        from datetime import datetime
        
        # Read the file content
        with open(file_path, 'rb') as f:
            binary_data = f.read()
        
        # Get file metadata
        filename = os.path.basename(file_path)
        content_type = 'video/mp4'
        file_size = len(binary_data)
        
        # Create database record
        video_asset = VideoAsset(
            path=None,  # No path since stored in DB
            is_uploaded=False,
            created_at=datetime.now(),
            binary_data=binary_data,
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            extras={"prompt": prompt}
        )
        
        # Save to database using async session
        async_gen = get_async_session()
        session = await async_gen.__anext__()
        try:
            session.add(video_asset)
            await session.commit()
            await session.refresh(video_asset)
        finally:
            await async_gen.aclose()
        
        # Delete local file after successful DB save
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[DB SAVE VIDEO] ✓ Deleted local file: {file_path}")
        except Exception as e:
            print(f"[DB SAVE VIDEO] ⚠️ Could not delete local file: {e}")
        
        print(f"[DB SAVE VIDEO] ✓ Saved to database with ID: {video_asset.id}")
        return video_asset

MANIM_SERVICE = ManimService()
