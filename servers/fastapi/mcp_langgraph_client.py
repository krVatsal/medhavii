import asyncio
import json
import os
import traceback
from typing import Any, Dict, List, Optional, Type

from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq

load_dotenv()

from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field, create_model

# Ensure you have set GROQ_API_KEY in your environment variables

def json_schema_to_pydantic(name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
    """
    Convert a JSON schema to a Pydantic model.
    This is a simplified converter and might need expansion for complex schemas.
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
            
            # Handle required fields
            if field_name in schema.get("required", []):
                fields[field_name] = (field_type, Field(description=field_info.get("description", "")))
            else:
                fields[field_name] = (Optional[field_type], Field(default=None, description=field_info.get("description", "")))
    
    return create_model(f"{name}Args", **fields)

async def main():
    # Configuration for the Manim MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["C:/Users/kumar/Downloads/manim-mcp-server-main/manim-mcp-server-main/src/manim_server.py"],
        env={
            **os.environ,
            "MANIM_EXECUTABLE": "C:/Users/kumar/AppData/Local/Programs/Python/Python312/Scripts/manim.exe"
        }
    )
    
    print("Connecting to MCP server (stdio)...")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("Connected to MCP server.")
                await session.initialize()
                
                # List available tools
                result = await session.list_tools()
                tools_data = result.tools
                print(f"Found {len(tools_data)} tools.")
                
                langchain_tools = []
                
                for tool in tools_data:
                    print(f" - {tool.name}: {tool.description}")
                    
                    # Create Pydantic model for arguments
                    args_schema = json_schema_to_pydantic(tool.name, tool.inputSchema)
                    
                    # Define the tool function
                    # We need to capture tool.name in the closure
                    async def make_tool_func(t_name: str):
                        async def tool_func(**kwargs):
                            print(f"Calling tool {t_name} with args: {kwargs}")
                            try:
                                result = await session.call_tool(t_name, arguments=kwargs)
                                # Combine text content from result
                                output = "\n".join([c.text for c in result.content if c.type == "text"])
                                return output
                            except Exception as e:
                                return f"Error calling tool: {str(e)}"
                        return tool_func

                    tool_coroutine = await make_tool_func(tool.name)

                    # Create LangChain tool
                    lc_tool = StructuredTool.from_function(
                        func=None, # We only provide coroutine
                        coroutine=tool_coroutine,
                        name=tool.name,
                        description=tool.description or "",
                        args_schema=args_schema
                    )
                    langchain_tools.append(lc_tool)
                
                if not langchain_tools:
                    print("No tools found. Exiting.")
                    return

                # Initialize LLM
                # Make sure GROQ_API_KEY is set
                if not os.getenv("GROQ_API_KEY"):
                    print("Warning: GROQ_API_KEY not found in environment variables.")
                
                llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
                
                # Create LangGraph Agent
                graph = create_react_agent(llm, tools=langchain_tools)
                
                print("\nAgent ready. Enter a query (or 'q' to quit):")
                
                while True:
                    user_input = input("> ")
                    if user_input.lower() in ["q", "quit", "exit"]:
                        break
                    
                    inputs = {"messages": [("user", user_input)]}
                    
                    print("Processing...")
                    # Increase recursion limit to prevent errors
                    config = {"recursion_limit": 50}
                    async for event in graph.astream(inputs, config=config, stream_mode="values"):
                        message = event.get("messages")[-1]
                        if hasattr(message, "content"):
                            print(f"Agent: {message.content}")
                        else:
                            print(message)

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
