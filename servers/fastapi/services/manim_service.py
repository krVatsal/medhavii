import asyncio
import json
import os
import traceback
from typing import Any, Dict, List, Optional, Type
import uuid

from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field, create_model

from models.sql.video_asset import VideoAsset
from utils.asset_directory_utils import get_videos_directory

load_dotenv()

def json_schema_to_pydantic(name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
    """
    Convert a JSON schema to a Pydantic model.
    """
    fields = {}
    if "properties" in schema:
        for field_name, field_info in schema["properties"].items():
            field_type = str
            if field_info.get("type") == "integer":
                field_type = int
            elif field_info.get("type") == "number":
                field_type = float
            elif field_info.get("type") == "boolean":
                field_type = bool
            elif field_info.get("type") == "array":
                field_type = list
            elif field_info.get("type") == "object":
                field_type = dict
            
            if field_name in schema.get("required", []):
                fields[field_name] = (field_type, Field(description=field_info.get("description", "")))
            else:
                fields[field_name] = (Optional[field_type], Field(default=None, description=field_info.get("description", "")))
    
    return create_model(f"{name}Args", **fields)

class ManimService:
    def __init__(self):
        # TODO: Move these paths to configuration/env vars
        self.server_params = StdioServerParameters(
            command="python",
            args=["C:/Users/kumar/Downloads/manim-mcp-server-main/manim-mcp-server-main/src/manim_server.py"],
            env={
                **os.environ,
                "MANIM_EXECUTABLE": "C:/Users/kumar/AppData/Local/Programs/Python/Python312/Scripts/manim.exe"
            }
        )

    async def generate_video(self, prompt: str) -> Optional[VideoAsset]:
        print(f"Generating video for prompt: {prompt}")
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.list_tools()
                    tools_data = result.tools
                    
                    langchain_tools = []
                    
                    for tool in tools_data:
                        args_schema = json_schema_to_pydantic(tool.name, tool.inputSchema)
                        
                        async def make_tool_func(t_name: str):
                            async def tool_func(**kwargs):
                                print(f"Calling tool {t_name} with args: {kwargs}")
                                try:
                                    result = await session.call_tool(t_name, arguments=kwargs)
                                    output = "\n".join([c.text for c in result.content if c.type == "text"])
                                    return output
                                except Exception as e:
                                    return f"Error calling tool: {str(e)}"
                            return tool_func

                        tool_coroutine = await make_tool_func(tool.name)

                        lc_tool = StructuredTool.from_function(
                            func=None,
                            coroutine=tool_coroutine,
                            name=tool.name,
                            description=tool.description or "",
                            args_schema=args_schema
                        )
                        langchain_tools.append(lc_tool)
                    
                    if not langchain_tools:
                        print("No tools found.")
                        return None

                    if not os.getenv("GROQ_API_KEY"):
                        print("Warning: GROQ_API_KEY not found.")
                        return None
                    
                    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
                    graph = create_react_agent(llm, tools=langchain_tools)
                    
                    # We ask the agent to generate the video and return the file path
                    enhanced_prompt = f"{prompt}. After generating the video, please output the absolute file path of the generated video file."
                    
                    inputs = {"messages": [("user", enhanced_prompt)]}
                    config = {"recursion_limit": 50}
                    
                    final_message = None
                    async for event in graph.astream(inputs, config=config, stream_mode="values"):
                        message = event.get("messages")[-1]
                        final_message = message
                    
                    if final_message and hasattr(final_message, "content"):
                        content = final_message.content
                        print(f"Agent response: {content}")
                        
                        # Try to extract file path from content
                        # This is a heuristic. We might need a more robust way.
                        # Assuming the agent mentions the path or the tool output contains it.
                        # For now, let's look for .mp4 extension
                        import re
                        match = re.search(r'(?:[a-zA-Z]:)?[\\/][^:?*<>|"\n]+\.mp4', content)
                        if match:
                            video_path = match.group(0)
                            # Verify if file exists
                            if os.path.exists(video_path):
                                # Copy to our media directory
                                filename = f"{uuid.uuid4()}.mp4"
                                dest_path = os.path.join(get_videos_directory(), filename)
                                import shutil
                                shutil.copy2(video_path, dest_path)
                                
                                return VideoAsset(
                                    path=dest_path,
                                    is_uploaded=False,
                                    extras={"original_path": video_path, "prompt": prompt, "url": f"/media/videos/{filename}"}
                                )
                        
                        # If regex didn't match, maybe the tool output had it but agent didn't repeat it explicitly?
                        # But we only have the agent's final response here.
                        
        except Exception as e:
            print(f"Error generating video: {e}")
            traceback.print_exc()
            return None
        
        return None

MANIM_SERVICE = ManimService()
