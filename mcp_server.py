#!/usr/bin/env python3
"""
MCP Server - Provides tools via Model Context Protocol
This server exposes basic tools like calculator, time, and text operations
"""

import json
import sys
import datetime
import asyncio
from typing import Any, Dict, List, Optional


class MCPServer:
    """Simple MCP Server implementation"""
    
    def __init__(self, name: str):
        self.name = name
        self.tools = {}
        
    def tool(self, func):
        """Decorator to register a tool"""
        tool_name = func.__name__
        self.tools[tool_name] = {
            "name": tool_name,
            "description": func.__doc__ or f"Tool: {tool_name}",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "func": func
        }
        
        # Extract parameters from function signature
        import inspect
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            # Simple type mapping
            param_type = "string"
            if param.annotation:
                if param.annotation == float or param.annotation == int:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                    
            self.tools[tool_name]["inputSchema"]["properties"][param_name] = {
                "type": param_type
            }
            if param.default == inspect.Parameter.empty:
                self.tools[tool_name]["inputSchema"]["required"].append(param_name)
                
        return func
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a JSON-RPC request"""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id", 1)
        
        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "protocolVersion": "1.0.0",
                        "serverInfo": {
                            "name": self.name,
                            "version": "1.0.0"
                        }
                    },
                    "id": request_id
                }
                
            elif method == "tools/list":
                tools_list = []
                for tool_name, tool_info in self.tools.items():
                    tools_list.append({
                        "name": tool_name,
                        "description": tool_info["description"],
                        "inputSchema": tool_info["inputSchema"]
                    })
                return {
                    "jsonrpc": "2.0",
                    "result": {"tools": tools_list},
                    "id": request_id
                }
                
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name not in self.tools:
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": f"Tool not found: {tool_name}"
                        },
                        "id": request_id
                    }
                
                # Call the tool
                func = self.tools[tool_name]["func"]
                if asyncio.iscoroutinefunction(func):
                    result = await func(**arguments)
                else:
                    result = func(**arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": str(result)
                            }
                        ]
                    },
                    "id": request_id
                }
                
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": request_id
            }
            
    async def run_stdio(self):
        """Run the server using stdio transport"""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        
        while True:
            try:
                # Read a line from stdin
                line = await reader.readline()
                if not line:
                    break
                    
                # Parse the JSON-RPC request
                request = json.loads(line.decode().strip())
                
                # Handle the request
                response = await self.handle_request(request)
                
                # Send the response
                response_line = json.dumps(response) + "\n"
                sys.stdout.write(response_line)
                sys.stdout.flush()
                
            except Exception as e:
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    },
                    "id": None
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()


# Create the server instance
server = MCPServer("basic-tools")


# Tool implementations
@server.tool
async def add(a: float, b: float) -> float:
    """Add two numbers together"""
    return a + b


@server.tool
async def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b


@server.tool
async def get_current_time() -> str:
    """Get the current date and time"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@server.tool
async def uppercase(text: str) -> str:
    """Convert text to uppercase"""
    return text.upper()


@server.tool
async def lowercase(text: str) -> str:
    """Convert text to lowercase"""
    return text.lower()


@server.tool
async def count_words(text: str) -> int:
    """Count the number of words in text"""
    return len(text.split())


@server.tool
async def reverse_text(text: str) -> str:
    """Reverse the given text"""
    return text[::-1]


async def main():
    """Run the MCP server using stdio transport"""
    await server.run_stdio()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())