"""
Production Accounts MCP Server - Provides real trading capabilities via Model Context Protocol.
This replaces the simulated accounts_server.py with real Alpaca trading integration.
Now supports trader-specific API credentials for separate account management.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from core.production_accounts import ProductionAccount
from utils.database import write_log
from typing import Dict, Any, List
from dotenv import load_dotenv
import os
import json

load_dotenv()

mcp = FastMCP("Production Trading Accounts")

# Trading mode configuration
paper_trading = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"
execute_real_orders = os.getenv("EXECUTE_REAL_ORDERS", "false").lower() == "true"

# Cache for trader accounts to avoid recreating them
_trader_accounts = {}

def get_trader_account(name: str) -> ProductionAccount:
    """Get or create a trader-specific ProductionAccount instance"""
    if name not in _trader_accounts:
        _trader_accounts[name] = ProductionAccount(name, paper_trading=paper_trading)
    return _trader_accounts[name]

@mcp.tool()
async def buy_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """
    Execute buy order through Alpaca with risk management using trader-specific account.
    
    Args:
        name: Trader account name
        symbol: Stock ticker symbol (e.g., 'AAPL')
        quantity: Number of shares to buy (must be positive)
        rationale: Reason for the trade for compliance and analysis
    
    Returns:
        String with order result and updated portfolio status
    """
    try:
        # Get trader-specific account
        account = get_trader_account(name)
        
        # Execute buy order through trader's specific account
        result = account.buy_shares(symbol.upper(), quantity, rationale)
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Buy order system error: {str(e)}"
        write_log(name, "error", error_msg)
        return error_msg

@mcp.tool()
async def sell_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """
    Execute sell order through Alpaca with risk management using trader-specific account.
    
    Args:
        name: Trader account name
        symbol: Stock ticker symbol (e.g., 'AAPL')
        quantity: Number of shares to sell (must be positive)
        rationale: Reason for the trade for compliance and analysis
    
    Returns:
        String with order result and updated portfolio status
    """
    try:
        # Get trader-specific account
        account = get_trader_account(name)
        
        # Execute sell order through trader's specific account
        result = account.sell_shares(symbol.upper(), quantity, rationale)
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Sell order system error: {str(e)}"
        write_log(name, "error", error_msg)
        return error_msg

@mcp.tool()
async def get_account_info(name: str) -> str:
    """
    Get comprehensive account information and portfolio status using trader-specific account.
    
    Args:
        name: Trader account name
    
    Returns:
        Detailed account report with real-time data
    """
    try:
        # Get trader-specific account
        account = get_trader_account(name)
        
        # Get account info from trader's specific Alpaca connection
        account_data = account.alpaca.get_account_info()
        positions = account.alpaca.get_positions()
        recent_orders = account.alpaca.get_orders(limit=10)
        
        result = {
            "account_name": name,
            "cash": float(account_data.get('cash', 0)),
            "portfolio_value": float(account_data.get('portfolio_value', 0)),
            "buying_power": float(account_data.get('buying_power', 0)),
            "equity": float(account_data.get('equity', 0)),
            "positions": positions,
            "recent_orders": recent_orders[:5],  # Last 5 orders
            "paper_trading": paper_trading,
            "execute_real_orders": execute_real_orders
        }
        
        write_log(name, "account", "Retrieved account details from trader-specific Alpaca connection")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"❌ Error getting account info: {str(e)}"

@mcp.tool()
async def sync_account_with_broker(name: str) -> str:
    """
    Synchronize account state with Alpaca broker account using trader-specific connection.
    
    Args:
        name: Trader account name
    
    Returns:
        String with sync result status
    """
    try:
        # Get trader-specific account and sync
        account = get_trader_account(name)
        result = account.sync_with_alpaca()
        return result
    
    except Exception as e:
        error_msg = f"❌ Sync check failed: {str(e)}"
        write_log(name, "error", error_msg)
        return error_msg

@mcp.tool()
async def get_portfolio_summary(name: str) -> Dict[str, Any]:
    """
    Get structured portfolio data for programmatic use using trader-specific account.
    
    Args:
        name: Trader account name
    
    Returns:
        Dictionary with portfolio metrics and holdings
    """
    try:
        # Get trader-specific account
        account = get_trader_account(name)
        
        # Get data from trader's specific Alpaca connection
        account_data = account.alpaca.get_account_info()
        positions = account.alpaca.get_positions()
        
        # Calculate holdings dictionary
        holdings = {}
        for pos in positions:
            if pos['qty'] != 0:
                holdings[pos['symbol']] = pos['qty']
        
        return {
            "account_name": name,
            "cash_balance": float(account_data['cash']),
            "portfolio_value": float(account_data['portfolio_value']),
            "buying_power": float(account_data['buying_power']),
            "equity": float(account_data['equity']),
            "holdings_count": len(holdings),
            "holdings": holdings,
            "paper_trading": paper_trading,
            "real_orders_enabled": execute_real_orders
        }
    
    except Exception as e:
        return {"error": f"Failed to get portfolio summary: {str(e)}"}

@mcp.tool()
async def get_recent_transactions(name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent trading transactions for analysis using trader-specific account.
    
    Args:
        name: Trader account name
        limit: Maximum number of transactions to return
    
    Returns:
        List of recent transaction dictionaries
    """
    try:
        # Get trader-specific account
        account = get_trader_account(name)
        
        # Get orders from trader's specific Alpaca connection
        orders = account.alpaca.get_orders(status="filled", limit=limit)
        
        return [
            {
                "symbol": order["symbol"],
                "quantity": order["qty"],
                "filled_qty": order.get("filled_qty", 0),
                "avg_price": order.get("avg_fill_price", 0),
                "total_value": order.get("filled_qty", 0) * order.get("avg_fill_price", 0) if order.get("avg_fill_price") else 0,
                "action": order["side"].upper(),
                "timestamp": order.get("filled_at", order.get("submitted_at", "")),
                "status": order["status"]
            }
            for order in orders
        ]
    
    except Exception as e:
        return [{"error": f"Failed to get transactions: {str(e)}"}]

@mcp.tool()
async def get_strategy(name: str) -> str:
    """
    Get current investment strategy for the account using trader-specific account.
    
    Args:
        name: Trader account name
    
    Returns:
        Current investment strategy description
    """
    try:
        # Get trader-specific account
        account = get_trader_account(name)
        strategy = account.get_strategy()
        write_log(name, "strategy", "Retrieved strategy from trader-specific account")
        return strategy
    
    except Exception as e:
        return f"❌ Error getting strategy: {str(e)}"

@mcp.tool()
async def change_strategy(name: str, strategy: str) -> str:
    """
    Update investment strategy for the account using trader-specific account.
    
    Args:
        name: Trader account name
        strategy: New investment strategy description
    
    Returns:
        Confirmation of strategy update
    """
    try:
        # Get trader-specific account
        account = get_trader_account(name)
        result = account.change_strategy(strategy)
        return result
    
    except Exception as e:
        return f"❌ Error changing strategy: {str(e)}"

@mcp.tool()
async def get_position_details(name: str, symbol: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific position using trader-specific account.
    
    Args:
        name: Trader account name
        symbol: Stock ticker symbol
    
    Returns:
        Dictionary with position details and current market data
    """
    try:
        # Get trader-specific account
        account = get_trader_account(name)
        
        symbol = symbol.upper()
        positions = account.alpaca.get_positions()
        
        # Find the position
        position = None
        for pos in positions:
            if pos['symbol'] == symbol:
                position = pos
                break
        
        if not position or position['qty'] == 0:
            return {"symbol": symbol, "quantity": 0, "message": "No position in this symbol"}
        
        current_price = account.get_real_price(symbol)
        
        return {
            "symbol": symbol,
            "quantity": position['qty'],
            "current_price": current_price,
            "market_value": position['market_value'],
            "average_cost": position['avg_entry_price'],
            "unrealized_pl": position['unrealized_pl'],
            "unrealized_pl_percent": position['unrealized_plpc'] * 100
        }
    
    except Exception as e:
        return {"symbol": symbol, "error": f"Failed to get position details: {str(e)}"}

@mcp.tool()
async def get_trading_status() -> Dict[str, Any]:
    """
    Get current trading system status and configuration.
    
    Returns:
        Dictionary with system status information
    """
    try:
        account_data = get_account_info()
        
        return {
            "paper_trading": paper_trading,
            "real_orders_enabled": execute_real_orders,
            "alpaca_account_status": account_data.get('status', 'unknown'),
            "portfolio_value": float(account_data.get('portfolio_value', 0)),
            "risk_limits": {
                "max_position_size": float(os.getenv("MAX_POSITION_SIZE", "1000")),
                "max_daily_trades": int(os.getenv("MAX_DAILY_TRADES", "10"))
            },
            "system_status": "operational"
        }
    
    except Exception as e:
        return {"system_status": "error", "error": str(e)}

if __name__ == "__main__":
    print(f"🚀 Starting Production Accounts MCP Server")
    print(f"   Paper Trading: {paper_trading}")
    print(f"   Real Orders: {execute_real_orders}")
    print(f"   Risk Management: Enabled")
    
    mcp.run(transport="stdio")
