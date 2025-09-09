#!/usr/bin/env python3
"""
MCP Server - Provides tools via Model Context Protocol over HTTP
This server exposes basic tools like calculator, time, and text operations
"""

import json
import datetime
import asyncio
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


class ToolRequest(BaseModel):
    tool: str
    args: Dict[str, Any] = {}


class ToolListResponse(BaseModel):
    tools: list


class ToolCallResponse(BaseModel):
    result: str


class ErrorResponse(BaseModel):
    error: str


class SimpleMCPServer:
    """Simplified MCP Server implementation with HTTP API"""
    
    def __init__(self):
        self.tools = {}
        self.app = FastAPI(title="MCP Server", version="1.0.0")
        self.setup_routes()
        
    def tool(self, func):
        """Decorator to register a tool"""
        self.tools[func.__name__] = func
        return func
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/tools", response_model=ToolListResponse)
        async def list_tools():
            """List available tools"""
            return ToolListResponse(
                tools=[
                    {"name": name, "description": func.__doc__ or ""}
                    for name, func in self.tools.items()
                ]
            )
        
        @self.app.post("/tools/call", response_model=ToolCallResponse)
        async def call_tool(request: ToolRequest):
            """Call a specific tool"""
            tool_name = request.tool
            args = request.args
            
            if tool_name not in self.tools:
                raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
            
            try:
                result = await self.tools[tool_name](**args)
                return ToolCallResponse(result=str(result))
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the HTTP server"""
        print(f"Starting MCP server on http://{host}:{port}")
        print("Available tools:")
        for name, func in self.tools.items():
            print(f"  - {name}: {func.__doc__ or 'No description'}")
        
        uvicorn.run(self.app, host=host, port=port, log_level="info")


# Create server and register tools
server = SimpleMCPServer()


@server.tool
async def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b


@server.tool
async def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b


@server.tool
async def get_current_time() -> str:
    """Get current date and time"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@server.tool
async def uppercase(text: str) -> str:
    """Convert text to uppercase"""
    return text.upper()


@server.tool
async def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())


if __name__ == "__main__":
    server.run()