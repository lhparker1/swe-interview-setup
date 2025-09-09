# MCP Agent System (Simplified)

A straightforward two-file Python system demonstrating Model Context Protocol (MCP) with a LangGraph agent.

## What's Been Simplified

1. **Minimal Protocol**: Simple JSON messages instead of full JSON-RPC
2. **Less Boilerplate**: Removed complex type schemas and protocol negotiations  
3. **Cleaner Code**: Reduced from ~300 to ~170 lines total
4. **Fewer Tools**: Just the essentials to demonstrate the pattern

## Architecture

1. **`mcp_server.py`** - Simple tool server that reads/writes JSON via stdio
2. **`agent_cli.py`** - LangGraph agent that spawns the server and provides a CLI

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=your-key-here
   ```

3. Run the agent:
   ```bash
   python agent_cli.py
   ```

## How It Works

The system uses a simple protocol:
- **List tools**: `{"method": "list_tools"}` → Returns available tools
- **Call tool**: `{"method": "call_tool", "tool": "add", "args": {"a": 1, "b": 2}}` → Returns result

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

## Adding New Tools

Just add a function to `mcp_server.py`:

```python
@server.tool
async def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"
```

The agent will automatically discover it on next run.