# AI Trading Bot Development Guide

A production-ready autonomous trading system powered by AI agents, real-time market data, and comprehensive risk management. This system uses the Alpaca Trade API for actual market operations with sophisticated AI decision-making capabilities.

## Project Architecture

### Core Structure
- **src/**: Main source directory containing all production components
- **pyproject.toml**: Uses `uv` package manager with production-focused dependencies (OpenAI, Anthropic, Alpaca Trade API)
- **Environment**: Production-ready system with paper trading safety and live trading capability

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

#### Production Trading Architecture
- **Trading Agents**: Use OpenAI and Anthropic models with MCP servers for real market operations
- **Market Research**: Dual search capabilities via Serper (Google) + Brave Search APIs
- **Risk Management**: Built-in position limits, trade validation, and portfolio risk controls
- **Real Trading**: Alpaca Trade API integration with paper trading safety

### Critical Development Patterns

#### Environment Configuration
Always use `.env` files with these key variables:
- Trading API keys (ALPACA_KEY, ALPACA_SECRET)
- AI model keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)  
- Search API keys (SERPER_API_KEY, BRAVE_API_KEY)
- Safety controls (ALPACA_PAPER_TRADING=true, EXECUTE_REAL_ORDERS=false)
- Risk limits (MAX_POSITION_SIZE, MAX_DAILY_TRADES, MAX_PORTFOLIO_RISK)

#### MCP Server Parameters (mcp_params.py)
Production servers are configured via command arrays:
```python
trader_mcp_server_params = [
    {"command": "uv", "args": ["run", "alpaca_server.py"]},
    {"command": "uv", "args": ["run", "production_accounts_server.py"]},
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
- SQLite via `accounts.db` for account and transaction tracking
- Production account persistence through `production_accounts.py` with Alpaca sync
- Real-time logging system via `database.py` and simplified `tracers.py`

### UI Layer
Gradio-based dashboard (`app.py`) with:
- Real-time portfolio monitoring with live Alpaca data
- Transaction history tracking with actual trade records
- Risk management status and limit monitoring
- Auto-refresh timers and async updates

### Testing & Debugging
- Comprehensive test suite via `test_system.py`
- Simplified logging/tracing system via `tracers.py`
- Gradio UI provides real-time debugging of agent decisions
- Environment flags control paper vs live trading

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

## Production Trading Features

### Real Market Integration
- **Alpaca API**: Live market data and order execution
- **Paper Trading**: Safe testing environment with real data
- **Risk Controls**: Position limits, daily trade limits, portfolio risk management
- **Account Sync**: Real-time balance and position tracking

### Safety & Risk Management
- **Default Paper Trading**: All operations in safe simulation mode
- **Order Validation**: Pre-execution risk checks and position limits
- **Trade Logging**: Complete audit trail of all decisions and executions
- **Error Handling**: Comprehensive error handling with graceful degradation

### Testing & Validation
- **System Tests**: Comprehensive test suite via `test_system.py`
- **Component Tests**: Individual MCP server testing
- **Integration Tests**: End-to-end trading flow validation
- **Risk Testing**: Position limit and risk control validation

## Important Conventions

- Always use async/await for agent operations
- MCP servers run as separate processes - handle connection timeouts gracefully
- Environment variables control behavior - never hardcode configuration
- Use structured logging with trace IDs for debugging complex agent interactions
- Follow the existing naming patterns: `{name}_server.py` for servers, `{name}_client.py` for client utilities
- **CRITICAL**: Always test with paper trading before enabling real money trading
- **SAFETY FIRST**: All production operations must validate risk limits before execution