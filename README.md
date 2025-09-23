# AI Trading Bot - Production Ready System

A sophisticated autonomous trading system powered by AI agents, real-time market data, and comprehensive risk management. This system has been transformed from an educational simulation into a production-ready trading platform using Alpaca's trading API.

## 🚀 System Overview

This is a **production-ready AI trading system** that combines:
- **Real market data** via Alpaca Trade API
- **Dual AI models** (OpenAI + Anthropic) for diverse trading strategies
- **Comprehensive market research** through Serper (Google) + Brave Search
- **Risk management** with position limits and trade validation
- **Model Context Protocol (MCP)** for agent communication
- **Paper trading** safety with live trading capability

## 🏗️ System Architecture & Data Flow

### 📊 Architecture Overview

The system follows a **modular, layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                    🚀 ORCHESTRATION LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│  trading_floor.py  │  Creates traders, manages execution cycles │
│  app.py           │  Gradio dashboard for monitoring/control   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     🤖 AI AGENT LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  trading_agents/traders.py     │  Agent creation & execution    │
│  trading_agents/templates.py   │  AI instruction templates      │
│  trading_agents/tracers.py     │  Logging and tracing system    │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🔧 MCP TOOLS LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  servers/accounts_server.py    │  Trading & account tools       │
│  servers/alpaca_server.py      │  Market data tools             │
│  servers/push_server.py        │  Notification tools            │
│  models/ (Pydantic schemas)    │  Type-safe structured outputs  │
│  config/mcp_params.py          │  MCP server configurations     │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   💼 CORE BUSINESS LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│  core/alpaca_client.py         │  Main facade & orchestration   │
│  core/trading_client.py        │  Risk-managed order execution  │
│  core/account_client.py        │  Account & portfolio operations │
│  core/market_data_client.py    │  Price & market data           │
│  core/base_alpaca_client.py    │  Shared connection management   │
│  core/risk_manager.py          │  Advanced risk assessment      │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   🎯 STRATEGY & CONFIG LAYER                   │
├─────────────────────────────────────────────────────────────────┤
│  strategies/strategies.py      │  Trading strategies (Warren,   │
│  strategies/__init__.py        │  Ray, Cathie) with risk limits │
│  utils/database.py             │  Logging and data persistence   │
│  utils/util.py                 │  Helper functions               │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     🌐 EXTERNAL APIS                           │
├─────────────────────────────────────────────────────────────────┤
│  Alpaca Trading API            │  Live market data & execution  │
│  OpenAI/Anthropic APIs         │  AI model inference            │
│  Serper/Brave Search APIs      │  Market research & news        │
└─────────────────────────────────────────────────────────────────┘
```

### 🔄 Data Flow Diagram

```
1. STARTUP FLOW:
   trading_floor.py
   ├── Creates Trader instances (Warren, Ray, Cathie)
   ├── Each Trader gets strategy from strategies/strategies.py
   ├── AlpacaClient created with strategy-specific risk limits
   └── MCP servers started (accounts_server.py, alpaca_server.py)

2. TRADING CYCLE FLOW:
   Trader.run_trading_session()
   ├── Templates generate AI instructions with strategy context
   ├── Agent connects to MCP tools via mcp_params.py configuration
   ├── Agent uses tools: get_account_info, get_stock_price, buy_shares
   ├── MCP servers delegate to core clients:
   │   ├── accounts_server.py → AlpacaClient → TradingClient
   │   └── alpaca_server.py → AlpacaClient → MarketDataClient
   ├── TradingClient applies enhanced risk assessment
   ├── Risk-approved trades execute via Alpaca API
   └── Results logged via database.py

3. RISK MANAGEMENT FLOW:
   buy_shares_with_risk_management()
   ├── TradingClient.buy_shares_with_risk_management()
   ├── RiskManager.validate_trade(return_assessment=True)
   ├── Conviction-based position sizing (1-10 scale)
   ├── Real-time risk feedback (🟢🟡🟠🔴🚨)
   ├── Smart warnings and suggestions
   └── Trade execution or rejection with detailed feedback
```

### 🏗️ Core Components

```
src/
├── trading_agents/     # 🤖 AI Agent Layer
│   ├── traders.py      # Agent creation, MCP integration, execution
│   ├── templates.py    # Strategy-aware AI instruction templates
│   └── tracers.py      # Comprehensive logging and tracing
├── core/              # 💼 Core Business Layer
│   ├── alpaca_client.py        # Main facade with strategy integration
│   ├── trading_client.py       # Enhanced risk-managed trading
│   ├── account_client.py       # Account & portfolio operations
│   ├── market_data_client.py   # Real-time market data
│   ├── base_alpaca_client.py   # Shared connection management
│   └── risk_manager.py         # Advanced risk assessment system
├── servers/           # 🔧 MCP Tools Layer
│   ├── accounts_server.py      # Trading & account MCP tools
│   ├── alpaca_server.py        # Market data MCP tools
│   └── push_server.py          # Notification MCP tools
├── models/            # 📡 Pydantic Data Models
│   ├── account_models.py       # Account & portfolio structured outputs
│   ├── market_models.py        # Market data structured outputs
│   ├── trading_models.py       # Trading & risk structured outputs
│   └── notification_models.py  # Notification structured outputs
├── strategies/        # 🎯 Strategy Layer
│   ├── strategies.py           # Warren, Ray, Cathie strategies
│   └── __init__.py            # Strategy factory and registry
├── config/            # ⚙️ Configuration
│   └── mcp_params.py          # MCP server configurations
├── utils/             # 🛠️ Utilities
│   ├── database.py            # Logging and data persistence
│   └── util.py                # Helper functions and utilities
├── app.py            # 📊 Web Dashboard
└── trading_floor.py  # 🚀 Main Orchestrator
```

### 🔧 Component Integration

**Strategy → Client Integration:**
```python
# strategies/strategies.py defines Warren strategy
warren_strategy = Warren(max_position_size=1500)
risk_limits = warren_strategy.get_risk_limits()

# core/alpaca_client.py integrates strategy
client = AlpacaClient(trader_name="Warren")  # Auto-loads Warren strategy
client.risk_manager.risk_limits = warren_strategy.get_risk_limits()
```

**MCP Tools → Core Integration with Structured Outputs:**
```python
# servers/accounts_server.py exposes buy_shares tool with Pydantic response
@mcp.tool()
async def buy_shares(symbol, quantity, rationale, conviction_level=5) -> TradeResult:
    client = get_trader_client("Warren")  # Gets AlpacaClient
    result = client.buy_shares_with_risk_management(symbol, quantity, rationale, conviction_level)
    return TradeResult(
        success=result.success,
        message=result.message,
        trade_details=result.trade_details,
        risk_assessment=result.risk_assessment
    )

# core/trading_client.py handles execution with risk assessment
def buy_shares_with_risk_management(self, symbol, quantity, rationale, conviction_level=5):
    assessment = self.risk_manager.validate_trade(..., return_assessment=True)
    # Returns structured RiskAssessment model with type safety
    # Real-time risk feedback: 📊 Warren Risk Assessment: 🟡 low (Score: 35/100)
```

## 📊 Features

### ✅ Production Trading Capabilities
- **Real Market Data**: Live prices and market status via Alpaca
- **Paper Trading**: Safe simulation environment with real data
- **Live Trading**: Production capability (disabled by default)
- **Modular Architecture**: Specialized clients for market data, accounts, and trading

### ✅ AI-Powered Decision Making
- **Dual AI Models**: OpenAI GPT + Anthropic Claude for diverse strategies
- **Strategy Framework**: Injectable Warren, Ray, and Cathie strategies
- **Market Research**: Comprehensive news and sentiment analysis
- **Autonomous Trading**: Fully automated decision making and execution
- **Structured Data**: Type-safe Pydantic models for all tool responses

### ✅ Advanced Risk Management System
- **Enhanced Risk Scoring**: 0-100 risk scores with five intuitive levels (🟢🟡🟠🔴🚨)
- **Conviction-Based Trading**: Dynamic position sizing based on confidence (1-10 scale)
- **Pre-Trade Assessment**: Detailed risk analysis before execution
- **Real-Time Feedback**: Color-coded risk levels and smart suggestions
- **Intelligent Warnings**: Specific, actionable alerts with position recommendations
- **Performance Optimized**: Single-pass risk calculation for efficiency

### ✅ Comprehensive Research
- **Dual Search**: Serper (Google Search) + Brave Search APIs
- **News Analysis**: Real-time market news and sentiment
- **Technical Analysis**: Market data analysis and trend identification
- **Persistent Memory**: Research continuity across trading sessions

### ✅ Safety & Monitoring
- **Position Limits**: Strategy-specific maximum position sizes
- **Daily Limits**: Configurable maximum trades per day
- **Portfolio Risk**: Percentage-based portfolio risk controls
- **Complete Logging**: Comprehensive audit trail and decision tracking
- **Web Dashboard**: Real-time monitoring via Gradio interface

## 🔧 Setup & Installation

### Prerequisites
- Python 3.11+
- `uv` package manager (recommended) or `pip`
- Alpaca trading account (paper trading by default)
- API keys for AI models and search services

### Installation

1. **Clone and install dependencies:**
   ```bash
   git clone <repository>
   cd trader-bot
   uv sync  # or pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   Create a `.env` file with:
   ```env
   # Trading API
   ALPACA_KEY=your_alpaca_key
   ALPACA_SECRET=your_alpaca_secret
   ALPACA_PAPER_TRADING=true
   EXECUTE_REAL_ORDERS=false
   
   # AI Models
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   
   # Market Research
   SERPER_API_KEY=your_serper_key
   BRAVE_API_KEY=your_brave_key
   ```

3. **Run system tests:**
   ```bash
   cd src && uv run test_system.py
   ```

## 🚀 Usage

### Web Dashboard
Launch the Gradio web interface for monitoring:
```bash
cd src && uv run app.py
```

### Trading Floor
Run the main trading system:
```bash
cd src && uv run trading_floor.py
```

### MCP Servers
Start individual MCP servers for development/testing:
```bash
# Market data server
cd src/servers && uv run alpaca_server.py

# Trading execution server  
cd src/servers && uv run accounts_server.py
```

## 🔒 Safety & Risk Management

### Default Safety Settings
- **Paper Trading**: Enabled by default (no real money)
- **Real Orders**: Disabled by default
- **Position Limits**: $1,000 maximum per position
- **Daily Limits**: 10 trades maximum per day
- **Portfolio Risk**: 2% maximum portfolio risk

### Enhanced Risk Controls
- **Pre-trade Assessment**: Detailed risk analysis with scoring and recommendations
- **Conviction-Based Sizing**: Position sizes adjust based on trader confidence
- **Real-Time Feedback**: Live risk assessment during trading execution
- **Smart Warnings**: Actionable alerts when approaching risk limits
- **Account Synchronization**: Real-time balance and position tracking
- **Complete Audit Trail**: Comprehensive transaction and decision logging

### Risk Management Examples
```bash
# Example risk assessment output during trading:
📊 Warren Risk Assessment: 🟡 low (Score: 35/100)
⚠️  Risk Warnings: Position size ($1,400) is 93.3% of your limit
💡 Suggestion: Consider 6 shares instead of 8 for lower risk
✅ Buy 6 AAPL at $175.00 (Risk: low) - Strong earnings outlook

# Conviction-based position sizing:
Conviction 3/10: Recommends 3 shares ($525) - Conservative approach
Conviction 8/10: Recommends 6 shares ($1,050) - High confidence trade
Conviction 10/10: Recommends 7 shares ($1,225) - Maximum conviction
```

## ⚠️ Important Warnings

### Financial Risk
- **Paper Trading**: Use paper trading for testing and development
- **Real Money**: Only enable live trading after thorough testing
- **Position Limits**: Configure appropriate risk limits
- **Monitoring**: Always monitor system behavior

### API Costs
- **AI Models**: OpenAI and Anthropic charge per API call
- **Search APIs**: Serper and Brave have usage limits
- **Monitoring**: Track API usage and costs

## 📄 Disclaimer

This software is for educational and research purposes. Trading involves financial risk. Users are responsible for their own trading decisions and any financial outcomes. Always test thoroughly with paper trading before considering real money trading.

---

**🎯 Sophisticated AI Trading Platform with Advanced Risk Management**

*Production-ready system featuring modular architecture, conviction-based trading, and real-time risk assessment*