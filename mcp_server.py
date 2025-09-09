#!/usr/bin/env python3
"""
MCP Server - Provides tools via Model Context Protocol
This server exposes basic tools like calculator, time, and text operations
"""

import json
import sys
import datetime
import asyncio
from typing import Any, Dict


class SimpleMCPServer:
    """Simplified MCP Server implementation"""
    
    def __init__(self):
        self.tools = {}
        
    def tool(self, func):
        """Decorator to register a tool"""
        self.tools[func.__name__] = func
        return func
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming requests"""
        method = request.get("method")
        
        if method == "list_tools":
            # Return available tools
            return {
                "tools": [
                    {"name": name, "description": func.__doc__}
                    for name, func in self.tools.items()
                ]
            }
            
        elif method == "call_tool":
            # Execute a tool
            tool_name = request.get("tool")
            args = request.get("args", {})
            
            if tool_name in self.tools:
                result = await self.tools[tool_name](**args)
                return {"result": str(result)}
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        else:
            return {"error": f"Unknown method: {method}"}
            
    async def run(self):
        """Run the server - read JSON from stdin, write JSON to stdout"""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                    
                request = json.loads(line.strip())
                response = await self.handle_request(request)
                
                print(json.dumps(response))
                sys.stdout.flush()
                
            except Exception as e:
                print(json.dumps({"error": str(e)}))
                sys.stdout.flush()


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
    asyncio.run(server.run())