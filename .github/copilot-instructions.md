# AI Trading Bot Development Guide

A production-ready autonomous trading system powered by AI agents, real-time market data, and comprehensive risk management. This system uses the Alpaca Trade API for actual market operations with sophisticated AI decision-making capabilities.

## Project Architecture

### Core Structure
```
src/
├── trading_agents/     # AI agent logic and templates
├── servers/           # MCP servers for tool communication  
├── core/             # Trading engine and risk management
├── config/           # MCP server configuration
├── utils/            # Database, logging, utilities
├── memory/           # SQLite databases for agent persistence
└── app.py           # Gradio dashboard
```

### Key Components

#### MCP Server-Client Pattern
The project implements a distributed MCP architecture where AI agents communicate with specialized servers:

```python
# Server pattern (servers/*.py)
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
- **Trading Agents**: Use OpenAI/Anthropic models with structured templates (`templates.py`)
- **Market Research**: Dual search (Serper + Brave) + persistent memory via SQLite  
- **Risk Management**: Automatic validation via `RiskManager` class with configurable limits
- **Real Trading**: Modern `alpaca-py` library with paper/live trading modes

### Critical Development Patterns

#### Environment Configuration
Always use `.env` files with these key variables:
- Trading API keys (ALPACA_KEY, ALPACA_SECRET, or trader-specific like WARREN_ALPACA_KEY)
- AI model keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)  
- Search API keys (SERPER_API_KEY, BRAVE_API_KEY)
- Safety controls (ALPACA_PAPER_TRADING=true, EXECUTE_REAL_ORDERS=false)
- Risk limits (MAX_POSITION_SIZE, MAX_DAILY_TRADES, MAX_PORTFOLIO_RISK)

#### MCP Server Architecture (`config/mcp_params.py`)
Servers are configured as function-based parameter factories:
```python
def trader_mcp_server_params():
    return [
        {"command": "uv", "args": ["run", "servers/accounts_server.py"]},
        {"command": "uv", "args": ["run", "servers/push_server.py"]},
        {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"], "env": brave_env}
    ]
```

#### Trading Agent Pattern (`trading_agents/traders.py`)
Agents follow a strict workflow with mandatory risk checks:
```python
async def run_agent(self, trader_mcp_servers, researcher_mcp_servers):
    # STEP 1: Mandatory trading guidance check
    guidance = await self.get_trading_guidance()
    
    # STEP 2: Build enhanced message with risk context  
    enhanced_message = f"MANDATORY TRADING GUIDANCE:\n{guidance}\n\n{base_message}"
    
    # STEP 3: Run with structured templates
    await Runner.run(self.agent, enhanced_message, max_turns=MAX_TURNS)
```

#### AlpacaClient Integration (`core/alpaca_client.py`)
Modern `alpaca-py` library with integrated risk management:
```python
client = AlpacaClient(paper_trading=True, trader_name="Warren")
result = client.buy_shares_with_risk_management(symbol, quantity, rationale)
# Risk validation happens automatically before trade execution
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
- Agent memory databases in `memory/` directory (`Warren.db`, `Ray.db`, `Cathie.db`)
- Real-time logging system via `utils/database.py` and simplified `trading_agents/tracers.py`
- Direct Alpaca API integration for live account/position synchronization

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
2. Update `config/mcp_params.py` server configurations
3. Ensure proper async context management in agent initialization

### Model Integration
1. Add API client in `trading_agents/traders.py` following existing patterns
2. Update `get_model()` function with base URL and client mapping
3. Add to model arrays in `trading_floor.py`

### Agent Customization
Use `trading_agents/templates.py` for instruction prompts - separate researcher and trader instructions with dynamic content injection.

### Trader Management
- Each trader has dedicated credentials (e.g., `WARREN_ALPACA_KEY`) with fallback to generic
- Trader strategies defined in `utils/reset.py` and served via `accounts_server.py`
- Agent memory persisted in SQLite databases per trader (`memory/{name}.db`)

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

## Execution Commands

### Running the System
```bash
cd src && uv run trading_floor.py  # Main trading loop
cd src && uv run app.py           # Gradio dashboard
cd src && uv run test_system.py   # System tests
```

### MCP Server Testing
```bash
cd src/servers && uv run accounts_server.py  # Test accounts server
cd src/servers && uv run alpaca_server.py    # Test market data server
```

### Key Environment Variables
- `RUN_EVERY_N_MINUTES=60` - Trading cycle interval
- `USE_MIXED_MODELS=true` - Mix OpenAI/Anthropic models
- `DEFAULT_MODEL_PROVIDER=openai` - Default AI provider
- `RUN_EVEN_WHEN_MARKET_IS_CLOSED=false` - Weekend/holiday trading