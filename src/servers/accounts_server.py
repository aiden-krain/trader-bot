"""
Clean Accounts MCP Server - Direct AlpacaClient Integration.
Provides streamlined trading operations with integrated risk management.
Simple, focused architecture for production trading.
"""

import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from core.alpaca_client import AlpacaClient
from utils.database import write_log
from typing import Dict, Any, List
from dotenv import load_dotenv

# Import trader strategies from AlpacaClient to avoid circular imports
from core.alpaca_client import warren_strategy, ray_strategy, cathie_strategy

load_dotenv()

mcp = FastMCP("Accounts Server")

# Trading mode configuration
paper_trading = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"
execute_real_orders = os.getenv("EXECUTE_REAL_ORDERS", "false").lower() == "true"

# Simple cache for trader clients
_trader_clients = {}

# Strategy mapping
TRADER_STRATEGIES = {
    "Warren": warren_strategy,
    "Ray": ray_strategy,
    "Cathie": cathie_strategy
}

def get_trader_client(name: str) -> AlpacaClient:
    """Get or create trader-specific AlpacaClient"""
    if name not in _trader_clients:
        _trader_clients[name] = AlpacaClient(paper_trading=paper_trading, trader_name=name)
    return _trader_clients[name]

@mcp.tool()
async def buy_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """Execute buy order with integrated risk management"""
    try:
        client = get_trader_client(name)
        return client.buy_shares_with_risk_management(symbol.upper(), quantity, rationale)
    except Exception as e:
        error_msg = f"❌ Buy order error: {str(e)}"
        write_log(name, "error", error_msg)
        return error_msg

@mcp.tool()
async def sell_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """Execute sell order with integrated risk management"""
    try:
        client = get_trader_client(name)
        return client.sell_shares_with_risk_management(symbol.upper(), quantity, rationale)
    except Exception as e:
        error_msg = f"❌ Sell order error: {str(e)}"
        write_log(name, "error", error_msg)
        return error_msg

@mcp.tool()
async def get_account_info(name: str) -> str:
    """Get comprehensive account information with trading guidance"""
    try:
        client = get_trader_client(name)
        return client.get_trading_guidance()
    except Exception as e:
        error_msg = f"❌ Account info error: {str(e)}"
        write_log(name, "error", error_msg)
        return error_msg

@mcp.tool()
async def get_portfolio_summary(name: str) -> Dict[str, Any]:
    """Get portfolio summary with positions and account data"""
    try:
        client = get_trader_client(name)
        account_info = client.get_account_info()
        positions = client.get_positions()
        
        return {
            "trader": name,
            "cash": float(account_info.get('cash', 0)),
            "portfolio_value": float(account_info.get('portfolio_value', 0)),
            "buying_power": float(account_info.get('buying_power', 0)),
            "positions_count": len(positions),
            "positions": positions,
            "paper_trading": paper_trading
        }
    except Exception as e:
        write_log(name, "error", f"Portfolio summary error: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def get_portfolio_report(name: str) -> str:
    """Get detailed portfolio report"""
    try:
        client = get_trader_client(name)
        return client.get_portfolio_report()
    except Exception as e:
        error_msg = f"❌ Portfolio report error: {str(e)}"
        write_log(name, "error", error_msg)
        return error_msg

@mcp.tool()
async def get_real_price(name: str, symbol: str) -> Dict[str, Any]:
    """Get real-time price for a symbol"""
    try:
        client = get_trader_client(name)
        price = client.get_real_price(symbol.upper())
        return {
            "symbol": symbol.upper(),
            "price": price,
            "timestamp": "real-time"
        }
    except Exception as e:
        write_log(name, "error", f"Price lookup error: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def get_trading_guidance(name: str) -> str:
    """Get comprehensive trading guidance"""
    try:
        client = get_trader_client(name)
        return client.get_trading_guidance()
    except Exception as e:
        error_msg = f"❌ Trading guidance error: {str(e)}"
        write_log(name, "error", error_msg)
        return error_msg

@mcp.tool()
async def get_risk_status(name: str) -> Dict[str, Any]:
    """Get current risk management status"""
    try:
        client = get_trader_client(name)
        risk_summary = client.risk_manager.get_risk_summary()
        portfolio_value = client.calculate_portfolio_value()
        
        return {
            "trader": name,
            "risk_limits": risk_summary,
            "portfolio_value": portfolio_value,
            "status": "active"
        }
    except Exception as e:
        write_log(name, "error", f"Risk status error: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def get_trading_status() -> Dict[str, Any]:
    """Get overall trading system status"""
    return {
        "paper_trading": paper_trading,
        "execute_real_orders": execute_real_orders,
        "server_status": "active",
        "active_traders": len(_trader_clients),
        "risk_management": "enabled"
    }

@mcp.tool()
async def get_strategy(name: str) -> str:
    """Get investment strategy for a trader"""
    try:
        strategy = TRADER_STRATEGIES.get(name)
        if strategy:
            return strategy.strip()
        else:
            return f"No strategy found for trader {name}. Available traders: {', '.join(TRADER_STRATEGIES.keys())}"
    except Exception as e:
        error_msg = f"❌ Strategy retrieval error: {str(e)}"
        write_log(name, "error", error_msg)
        return error_msg

# Resource endpoints (simplified)
@mcp.resource("accounts://trader/{name}")
async def read_trader_resource(name: str) -> str:
    """Get trader account information as resource"""
    try:
        client = get_trader_client(name)
        return client.get_trading_guidance()
    except Exception as e:
        return f"❌ Error loading trader {name}: {str(e)}"

@mcp.resource("accounts://strategy/{name}")
async def read_strategy_resource(name: str) -> str:
    """Get trader investment strategy as resource"""
    strategy = TRADER_STRATEGIES.get(name)
    if strategy:
        return strategy.strip()
    else:
        return f"No strategy found for trader {name}. Available traders: {', '.join(TRADER_STRATEGIES.keys())}"

if __name__ == "__main__":
    print(f"🚀 Starting Accounts MCP Server")
    print(f"   Paper Trading: {paper_trading}")
    print(f"   Real Orders: {execute_real_orders}")
    print(f"   Architecture: Clean & Simple")
    
    mcp.run(transport="stdio")