"""
Trading MCP Server - Focused on trade execution and order management.
Provides clean trading operations with integrated risk management using TradingClient.
Trader-specific server that maintains individual trader contexts and strategies.
"""

import os
import sys

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from core.alpaca_client import AlpacaClient
from utils.database import write_log
from dotenv import load_dotenv

# Import Pydantic models for structured responses
from models import TradeResult, OrderCancellation

load_dotenv()

mcp = FastMCP("Trading Server")

# Trading mode configuration
paper_trading = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"
execute_real_orders = os.getenv("EXECUTE_REAL_ORDERS", "false").lower() == "true"

# Simple cache for trader clients
_trader_clients = {}

def get_trader_client(name: str) -> AlpacaClient:
    """Get or create trader-specific AlpacaClient with strategy injection"""
    if name not in _trader_clients:
        _trader_clients[name] = AlpacaClient(paper_trading=paper_trading, trader_name=name)
    return _trader_clients[name]

@mcp.tool()
async def buy_shares(name: str, symbol: str, quantity: int, rationale: str) -> TradeResult:
    """Execute buy order with integrated risk management using TradingClient"""
    try:
        client = get_trader_client(name)
        result_text = client.buy_shares_with_risk_management(symbol.upper(), quantity, rationale)
        
        # Parse the text result and create structured response
        success = "✅" in result_text and "❌" not in result_text
        
        return TradeResult(
            success=success,
            action="buy",
            symbol=symbol.upper(),
            quantity=quantity,
            rationale=rationale,
            message=result_text,
            error=None if success else result_text
        )
    except Exception as e:
        error_msg = f"❌ Buy order error: {str(e)}"
        write_log(name, "error", error_msg)
        return TradeResult(
            success=False,
            action="buy",
            symbol=symbol.upper(),
            quantity=quantity,
            rationale=rationale,
            message=error_msg,
            error=str(e)
        )

@mcp.tool()
async def sell_shares(name: str, symbol: str, quantity: int, rationale: str) -> TradeResult:
    """Execute sell order with integrated risk management using TradingClient"""
    try:
        client = get_trader_client(name)
        result_text = client.sell_shares_with_risk_management(symbol.upper(), quantity, rationale)
        
        # Parse the text result and create structured response
        success = "✅" in result_text and "❌" not in result_text
        
        return TradeResult(
            success=success,
            action="sell",
            symbol=symbol.upper(),
            quantity=quantity,
            rationale=rationale,
            message=result_text,
            error=None if success else result_text
        )
    except Exception as e:
        error_msg = f"❌ Sell order error: {str(e)}"
        write_log(name, "error", error_msg)
        return TradeResult(
            success=False,
            action="sell",
            symbol=symbol.upper(),
            quantity=quantity,
            rationale=rationale,
            message=error_msg,
            error=str(e)
        )

@mcp.tool()
async def cancel_order(name: str, order_id: str, rationale: str) -> OrderCancellation:
    """Cancel a specific order by ID with rationale using TradingClient"""
    try:
        client = get_trader_client(name)
        
        # Use TradingClient's cancel_order_by_id method
        result = client.trading.cancel_order_by_id(order_id, rationale)
        
        return OrderCancellation(
            success=result["success"],
            order_id=result["order_id"],
            symbol=result["symbol"],
            message=result["message"],
            error=result.get("error")
        )
        
    except Exception as e:
        error_msg = f"❌ Cancel order error: {str(e)}"
        write_log(name, "error", error_msg)
        return OrderCancellation(
            success=False,
            order_id=order_id,
            symbol="",
            message=error_msg,
            error=str(e)
        )

@mcp.tool()
async def cancel_all_orders(name: str, rationale: str) -> OrderCancellation:
    """Cancel all open orders with rationale using TradingClient"""
    try:
        client = get_trader_client(name)
        
        # Use TradingClient's cancel_all_orders method
        result = client.trading.cancel_all_orders(rationale)
        
        return OrderCancellation(
            success=result["success"],
            order_id="ALL",
            symbol="MULTIPLE",
            message=result["message"],
            error=result.get("error")
        )
        
    except Exception as e:
        error_msg = f"❌ Cancel all orders error: {str(e)}"
        write_log(name, "error", error_msg)
        return OrderCancellation(
            success=False,
            order_id="ALL",
            symbol="MULTIPLE",
            message=error_msg,
            error=str(e)
        )

# Resource endpoints for trading operations
@mcp.resource("trading://trader/{name}")
async def read_trader_trading_resource(name: str) -> str:
    """Get trader trading status and capabilities as resource"""
    try:
        client = get_trader_client(name)
        return f"Trading Status for {name}: Paper Trading={client.paper_trading}, Risk Management=Enabled"
    except Exception as e:
        return f"❌ Error loading trading status for {name}: {str(e)}"

if __name__ == "__main__":
    print(f"🚀 Starting Trading MCP Server")
    print(f"   Paper Trading: {paper_trading}")
    print(f"   Real Orders: {execute_real_orders}")
    print(f"   Focus: Trade Execution & Order Management")
    
    mcp.run(transport="stdio")
