# MCP Agent System

A two-file Python system that demonstrates Model Context Protocol (MCP) with a LangGraph agent.

## Architecture

1. **`mcp_server.py`** - MCP server that provides tools via stdio communication
2. **`agent_cli.py`** - LangGraph-based agent with CLI that connects to the MCP server

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your OpenAI API key:
   - Copy `.env.example` to `.env` (or edit the existing `.env`)
   - Add your OpenAI API key: `OPENAI_API_KEY=your-actual-key-here`

## Usage

1. **First terminal**: Run the agent CLI
   ```bash
   python agent_cli.py
   ```
   
   This will:
   - Start the MCP server as a subprocess
   - Connect to it via stdio
   - Show available tools
   - Provide a CLI for interaction

2. **Interact with the agent**: Type natural language commands
   ```
   You: What's 15 + 27?
   Agent: I'll add those numbers for you. 15 + 27 = 42

   You: What time is it?
   Agent: The current time is 2025-09-09 14:23:45

   You: Convert "hello world" to uppercase
   Agent: I'll convert that text to uppercase. "HELLO WORLD"
   ```

3. **Exit**: Type `quit`, `exit`, or `q`

## Available Tools

The MCP server provides these tools:
- `add(a, b)` - Add two numbers
- `multiply(a, b)` - Multiply two numbers  
- `get_current_time()` - Get current date/time
- `uppercase(text)` - Convert text to uppercase
- `lowercase(text)` - Convert text to lowercase
- `count_words(text)` - Count words in text
- `reverse_text(text)` - Reverse text

## How It Works

1. The agent CLI starts the MCP server as a subprocess
2. They communicate via JSON-RPC over stdio (stdin/stdout)
3. The agent discovers available tools from the MCP server
4. User input → LangGraph agent → LLM decides to use tools → MCP server executes → Results returned
5. The agent maintains conversation flow using LangGraph's graph structure

## Architecture Details

### MCP Server (`mcp_server.py`)
- Uses the `mcp` library to implement the Model Context Protocol
- Communicates via stdio (no networking required)
- Tools are defined as async functions with the `@server.tool()` decorator
- Handles JSON-RPC requests/responses

### Agent CLI (`agent_cli.py`)  
- Uses LangGraph to create a stateful agent
- Dynamically creates LangChain tools from MCP tool definitions
- Manages the MCP server lifecycle (starts/stops the subprocess)
- Provides a simple CLI interface

## Extending the System

To add new tools:
1. Add a new `@server.tool()` decorated function in `mcp_server.py`
2. The agent will automatically discover it on next run

To use a different LLM:
1. Modify the `ChatOpenAI` initialization in `agent_cli.py`
2. Update the API key setup accordingly

## Troubleshooting

- **"MCP client not connected"**: The MCP server failed to start. Check for Python errors.
- **"Tool error"**: The MCP server couldn't execute the tool. Check tool parameters.
- **No response from agent**: Ensure your OpenAI API key is set correctly in `.env`