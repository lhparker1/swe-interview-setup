#!/usr/bin/env python3
"""
Agent CLI - LangGraph-based agent that connects to MCP server
Provides a command-line interface for interacting with MCP tools
"""

import os
import sys
import asyncio
import subprocess
import json
from typing import Dict, Any, List, TypedDict, Annotated
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

# Load environment variables
load_dotenv()


class AgentState(TypedDict):
    """State for the agent graph"""
    messages: Annotated[List, add_messages]
    

class MCPClient:
    """Client to communicate with MCP server"""
    
    def __init__(self):
        self.process = None
        self.tools = {}
        
    async def connect(self):
        """Start the MCP server process and establish connection"""
        # Start the MCP server as a subprocess
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, "mcp_server.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Initialize connection by sending initialize request
        await self._send_request({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "clientInfo": {
                    "name": "agent-cli",
                    "version": "1.0.0"
                }
            },
            "id": 1
        })
        
        # Get available tools
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        })
        
        # Store tool definitions
        if "result" in response and "tools" in response["result"]:
            for tool_def in response["result"]["tools"]:
                self.tools[tool_def["name"]] = tool_def
                
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server and get response"""
        if not self.process:
            raise RuntimeError("MCP client not connected")
            
        # Send request
        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        return json.loads(response_line.decode())
        
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server"""
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 3
        })
        
        if "error" in response:
            raise Exception(f"Tool error: {response['error']}")
            
        return response.get("result", {}).get("content", [])
        
    async def disconnect(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()


# Global MCP client instance
mcp_client = MCPClient()


def create_mcp_tool(tool_name: str, tool_def: Dict[str, Any]):
    """Create a LangChain tool from MCP tool definition"""
    
    @tool
    async def mcp_tool(**kwargs):
        """Dynamic MCP tool"""
        result = await mcp_client.call_tool(tool_name, kwargs)
        # Extract text content from MCP response
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("text", str(result))
        return str(result)
    
    # Set tool name and description
    mcp_tool.__name__ = tool_name
    mcp_tool.__doc__ = tool_def.get("description", f"MCP tool: {tool_name}")
    
    return mcp_tool


async def create_agent():
    """Create the LangGraph agent with MCP tools"""
    # Connect to MCP server
    await mcp_client.connect()
    
    # Create LangChain tools from MCP tools
    tools = []
    for tool_name, tool_def in mcp_client.tools.items():
        tools.append(create_mcp_tool(tool_name, tool_def))
    
    # Initialize LLM (using OpenAI, but can be changed)
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Define the agent node
    async def agent(state: AgentState):
        """Agent node that calls the LLM"""
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}
    
    # Define conditional edge
    def should_continue(state: AgentState):
        """Check if we should continue to tools or end"""
        last_message = state["messages"][-1]
        if not last_message.tool_calls:
            return END
        return "tools"
    
    # Add nodes
    workflow.add_node("agent", agent)
    workflow.add_node("tools", ToolNode(tools))
    
    # Add edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    return workflow.compile()


async def main():
    """Main CLI loop"""
    print("Starting Agent CLI...")
    print("Connecting to MCP server...")
    
    try:
        # Create the agent
        agent = await create_agent()
        print("Connected! Available tools:")
        for tool_name in mcp_client.tools:
            print(f"  - {tool_name}")
        print("\nType 'quit' to exit\n")
        
        # CLI loop
        while True:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            if not user_input:
                continue
            
            # Process through agent
            try:
                state = {"messages": [HumanMessage(content=user_input)]}
                
                # Run the agent
                result = await agent.ainvoke(state)
                
                # Get the final message
                final_message = result["messages"][-1]
                
                # Print the response
                if isinstance(final_message, AIMessage):
                    print(f"Agent: {final_message.content}")
                    
            except Exception as e:
                print(f"Error: {e}")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect from MCP server
        print("\nDisconnecting from MCP server...")
        await mcp_client.disconnect()
        print("Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())