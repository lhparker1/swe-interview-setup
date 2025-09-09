# MCP Agent System - HTTP Architecture

A straightforward Python system demonstrating Model Context Protocol (MCP) over HTTP with a LangGraph agent.

## What's Changed

1. **HTTP Communication**: MCP server now runs as a FastAPI HTTP server instead of stdio
2. **Separate Processes**: Server and client run independently for better scalability
3. **RESTful API**: Clean HTTP endpoints for tool discovery and execution
4. **Better Error Handling**: HTTP status codes and structured error responses

## Architecture

1. **`mcp_server.py`** - FastAPI-based tool server with HTTP endpoints
2. **`agent_cli.py`** - LangGraph agent that connects to the server via HTTP

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=your-key-here
   ```

3. **Start the MCP server** (in one terminal):
   ```bash
   python mcp_server.py
   ```
   Server will start on http://127.0.0.1:8000

4. **Run the agent** (in another terminal):
   ```bash
   python agent_cli.py
   ```

## How It Works

The system uses HTTP REST API:
- **GET /tools** - List available tools
- **POST /tools/call** - Execute a tool with JSON payload: `{"tool": "add", "args": {"a": 1, "b": 2}}`

The agent automatically discovers tools from the server and creates LangChain tools for the LLM.

Example interaction:
```
You: What's 15 plus 27?
Agent: I'll add those numbers for you. 15 + 27 = 42

You: Make "hello" uppercase
Agent: HELLO
```

## Available Tools

- `add(a, b)` - Add two numbers
- `multiply(a, b)` - Multiply two numbers
- `get_current_time()` - Get current time
- `uppercase(text)` - Convert to uppercase
- `count_words(text)` - Count words

## API Endpoints

### GET /tools
Returns list of available tools:
```json
{
  "tools": [
    {"name": "add", "description": "Add two numbers"},
    {"name": "multiply", "description": "Multiply two numbers"}
  ]
}
```

### POST /tools/call
Execute a tool:
```json
// Request
{
  "tool": "add",
  "args": {"a": 5, "b": 3}
}

// Response
{
  "result": "8"
}
```

## Adding New Tools

Just add a function to `mcp_server.py`:

```python
@server.tool
async def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"
```

Restart the server and the agent will automatically discover the new tool.

## Benefits of HTTP Architecture

- **Scalability**: Server can handle multiple concurrent clients
- **Language Agnostic**: Any HTTP client can connect to the MCP server
- **Debugging**: Easy to test endpoints with curl or browser
- **Production Ready**: Can be deployed behind load balancers, with authentication, etc.