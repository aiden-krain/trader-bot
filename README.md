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

## 🏗️ Architecture

### Core Components

```
src/
├── agents/          # AI trading agents and logic
│   ├── traders.py   # Main trader agent implementation
│   ├── templates.py # AI instruction templates
│   └── tracers.py   # Logging and tracing system
├── core/            # Trading system core
│   ├── alpaca_client.py        # Real market data & trading
│   └── production_accounts.py  # Account management with risk controls
├── servers/         # MCP servers for agent communication
│   ├── alpaca_server.py             # Market data tools
│   └── accounts_server.py # Trading execution tools
├── config/          # System configuration
│   └── mcp_params.py # MCP server and search configurations
├── utils/           # Utilities
│   ├── database.py  # Data persistence and logging
│   └── util.py      # Helper functions
├── app.py          # Gradio web dashboard
└── trading_floor.py # Main orchestrator
```

### MCP (Model Context Protocol) Integration

The system uses MCP servers to provide AI agents with secure, validated access to:
- **Market Data**: Real-time prices, market status, stock search
- **Trading Operations**: Account management, order execution, portfolio tracking
- **Market Research**: Dual search capabilities via Serper + Brave Search

## 📊 Features

### ✅ Production Trading Capabilities
- **Real Market Data**: Live prices and market status via Alpaca
- **Paper Trading**: Safe simulation environment with real data
- **Live Trading**: Production capability (disabled by default)
- **Risk Management**: Position limits, daily trade limits, portfolio risk controls

### ✅ AI-Powered Decision Making
- **Dual AI Models**: OpenAI GPT + Anthropic Claude for diverse strategies
- **Market Research**: Comprehensive news and sentiment analysis
- **Autonomous Trading**: Fully automated decision making and execution

### ✅ Comprehensive Research
- **Dual Search**: Serper (Google Search) + Brave Search APIs
- **News Analysis**: Real-time market news and sentiment
- **Technical Analysis**: Market data analysis and trend identification

### ✅ Risk & Safety Controls
- **Position Limits**: Maximum position sizes per trade
- **Daily Limits**: Maximum number of trades per day
- **Portfolio Risk**: Maximum portfolio risk percentage
- **Validation**: All trades validated before execution

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
   
   # Risk Management
   MAX_POSITION_SIZE=1000
   MAX_DAILY_TRADES=10
   MAX_PORTFOLIO_RISK=0.02
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

### Risk Controls
- **Pre-trade validation**: All orders validated before execution
- **Account synchronization**: Real-time balance and position tracking
- **Error handling**: Comprehensive error handling and logging
- **Audit trail**: Complete transaction and decision logging

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

**🎯 Ready for Production Trading with AI-Powered Decision Making**