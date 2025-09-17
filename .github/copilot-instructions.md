# AI Agent Development Guide for trader-bot

This is a 6-week AI/Agentic Engineering course project focusing on autonomous AI agents, particularly Model Context Protocol (MCP) implementations for financial trading simulation.

## Project Architecture

### Core Structure
- **6_mcp/**: Week 6 MCP labs - the primary working directory containing the trading simulation
- **pyproject.toml**: Uses `uv` package manager with extensive AI/ML dependencies (OpenAI, Anthropic, LangChain, CrewAI, AutoGen, etc.)
- **Environment**: Designed for educational purposes with support for multiple AI model providers

### Key Components

#### MCP Server-Client Pattern
The project implements a distributed MCP architecture:

```python
# Server pattern (e.g., accounts_server.py, market_server.py)
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("server_name")

@mcp.tool()
async def tool_function(param: str) -> ReturnType:
    """Tool description for AI agents"""
    pass

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

#### Agent Architecture
- **Trader agents**: Use OpenAI Agents SDK with MCP servers for accounts, market data, and notifications
- **Researcher agents**: Separate agents with web search, fetch, and memory capabilities via MCP
- **Multi-model support**: GPT, DeepSeek, Gemini, Grok via different API endpoints

### Critical Development Patterns

#### Environment Configuration
Always use `.env` files with these key variables:
- API keys for multiple providers (OPENAI_API_KEY, DEEPSEEK_API_KEY, etc.)
- `USE_MANY_MODELS=true/false` - toggles between single/multi-model mode
- `RUN_EVERY_N_MINUTES` and `RUN_EVEN_WHEN_MARKET_IS_CLOSED` for simulation control

#### MCP Server Parameters (mcp_params.py)
Servers are configured via command arrays:
```python
trader_mcp_server_params = [
    {"command": "uv", "args": ["run", "accounts_server.py"]},
    {"command": "uvx", "args": ["mcp-server-fetch"]},
    {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"], "env": brave_env}
]
```

#### Async Context Management
Always use AsyncExitStack for MCP server lifecycle:
```python
async with AsyncExitStack() as stack:
    mcp_servers = [
        await stack.enter_async_context(MCPServerStdio(params))
        for params in server_params
    ]
```

### Package Management & Execution

- **Primary tool**: `uv` (not pip) - fast Python package manager
- **Server execution**: `uv run server_file.py` 
- **Package installation**: `uvx package_name` for tools, `uv tool install package` for CLI tools
- **Development**: Uses `uv.lock` for deterministic builds

### Windows Compatibility Note
MCP servers have known issues on Windows - WSL (Windows Subsystem for Linux) is the recommended workaround per setup documentation.

### Database & Persistence
- SQLite via `memory/` directory for individual agent memory
- Account data persistence through `accounts.py` with portfolio tracking
- Real-time logging system via `database.py` and `tracers.py`

### UI Layer
Gradio-based dashboard (`app.py`) with:
- Real-time portfolio monitoring
- Transaction history tracking  
- Multi-trader comparison views
- Auto-refresh timers and async updates

### Testing & Debugging
- Extensive logging/tracing system via `tracers.py`
- Gradio UI provides real-time debugging of agent decisions
- Environment flags control simulation vs real market data

## Common Development Tasks

### Adding New MCP Tools
1. Define in appropriate server file with `@mcp.tool()` decorator
2. Update `mcp_params.py` server configurations
3. Ensure proper async context management in agent initialization

### Model Integration
1. Add API client in `traders.py` following existing patterns
2. Update `get_model()` function with base URL and client mapping
3. Add to model arrays in `trading_floor.py`

### Agent Customization
Use `templates.py` for instruction prompts - separate researcher and trader instructions with dynamic content injection.

## Important Conventions

- Always use async/await for agent operations
- MCP servers run as separate processes - handle connection timeouts gracefully
- Environment variables control behavior - never hardcode configuration
- Use structured logging with trace IDs for debugging complex agent interactions
- Follow the existing naming patterns: `{name}_server.py` for servers, `{name}_client.py` for client utilities