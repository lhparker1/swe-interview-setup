#!/usr/bin/env python3
"""
Agent CLI - LangGraph-based agent that connects to MCP server via HTTP
Provides a command-line interface for interacting with MCP tools
"""

import os
import sys
import json
import asyncio
from typing import Dict, List, Any
from dotenv import load_dotenv
import httpx

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

# Load environment variables
load_dotenv()


class HTTPMCPClient:
    """HTTP-based MCP client"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.tools = []
        self.client = httpx.AsyncClient()
        
    async def connect(self):
        """Connect to MCP server and fetch available tools"""
        try:
            response = await self.client.get(f"{self.base_url}/tools")
            response.raise_for_status()
            data = response.json()
            self.tools = data.get("tools", [])
        except httpx.RequestError as e:
            raise ConnectionError(f"Could not connect to MCP server at {self.base_url}: {e}")
        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"HTTP error from MCP server: {e.response.status_code}")
        
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Call a tool on the MCP server"""
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/call",
                json={"tool": tool_name, "args": args}
            )
            response.raise_for_status()
            data = response.json()
            return data["result"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise Exception(f"Tool '{tool_name}' not found")
            elif e.response.status_code == 400:
                error_detail = e.response.json().get("detail", "Bad request")
                raise Exception(f"Tool execution error: {error_detail}")
            else:
                raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request error: {e}")
        
    async def disconnect(self):
        """Close the HTTP client"""
        await self.client.aclose()


def create_tools(mcp_client: HTTPMCPClient) -> List:
    """Create LangChain tools from MCP tools"""
    tools = []
    
    for tool_info in mcp_client.tools:
        tool_name = tool_info["name"]
        tool_desc = tool_info.get("description", f"MCP tool: {tool_name}")
        
        # Create a closure to capture the tool name and client
        def make_tool(name, desc, client):
            # Create the function with proper docstring
            async def mcp_tool(**kwargs):
                """Dynamically created MCP tool"""
                return await client.call_tool(name, kwargs)
            
            # Set function attributes
            mcp_tool.__name__ = name
            mcp_tool.__doc__ = desc
            
            # Apply the tool decorator (without name parameter)
            decorated_tool = tool(mcp_tool)
            # Manually set the name after decoration
            decorated_tool.name = name
            decorated_tool.description = desc
            
            return decorated_tool
            
        tools.append(make_tool(tool_name, tool_desc, mcp_client))
    
    return tools


async def main():
    """Main agent loop"""
    print("Starting Agent CLI...")
    print("Connecting to MCP server...")
    
    # Initialize MCP client
    mcp_client = HTTPMCPClient()
    
    try:
        # Connect to MCP server
        await mcp_client.connect()
        print(f"\nConnected to MCP server at {mcp_client.base_url}")
        print("Available tools:")
        for tool_info in mcp_client.tools:
            print(f"  - {tool_info['name']}: {tool_info.get('description', '')}")
        
        # Create tools
        tools = create_tools(mcp_client)
        
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0
        )
        
        # Create simple agent graph with proper message handling
        from langgraph.graph.message import add_messages
        from typing import Annotated
        
        class State(dict):
            messages: Annotated[list, add_messages]
        
        graph = StateGraph(State)
        
        # Agent node - calls LLM with tools
        async def agent(state):
            response = await llm.bind_tools(tools).ainvoke(state["messages"])
            return {"messages": [response]}
        
        # Tool execution node
        async def execute_tools(state):
            tool_calls = state["messages"][-1].tool_calls
            tool_messages = []
            
            for tool_call in tool_calls:
                # Find the matching tool
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # Execute the tool
                try:
                    result = await mcp_client.call_tool(tool_name, tool_args)
                    tool_messages.append({
                        "role": "tool",
                        "content": str(result),
                        "tool_call_id": tool_call["id"]
                    })
                except Exception as e:
                    tool_messages.append({
                        "role": "tool", 
                        "content": f"Error: {str(e)}",
                        "tool_call_id": tool_call["id"]
                    })
            
            return {"messages": tool_messages}
        
        # Conditional logic
        def should_continue(state):
            last_message = state["messages"][-1]
            return "tools" if getattr(last_message, 'tool_calls', None) else "__end__"
        
        # Add nodes
        graph.add_node("agent", agent)
        graph.add_node("tools", execute_tools)
        
        # Add edges
        graph.set_entry_point("agent")
        graph.add_conditional_edges("agent", should_continue)
        graph.add_edge("tools", "agent")
        
        # Compile
        app = graph.compile()
        
        print("\nReady! Type 'quit' to exit.")
        print("Note: Make sure the MCP server is running separately with: python mcp_server.py\n")
        
        # Main loop
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            if not user_input:
                continue
            
            # Run the agent
            try:
                result = await app.ainvoke({
                    "messages": [HumanMessage(content=user_input)]
                })
                
                # Print response
                final_message = result["messages"][-1]
                print(f"Agent: {final_message.content}")
                
            except Exception as e:
                print(f"Error: {e}")
    
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("\nDisconnecting...")
        await mcp_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())