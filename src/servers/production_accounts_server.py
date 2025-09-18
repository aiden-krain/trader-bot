"""
Production Accounts MCP Server - Provides real trading capabilities via Model Context Protocol.
This replaces the simulated accounts_server.py with real Alpaca trading integration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from core.production_accounts import ProductionAccount
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Production Trading Accounts")

# Global account instances for efficient reuse
accounts: Dict[str, ProductionAccount] = {}

# Trading mode configuration
paper_trading = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"
execute_real_orders = os.getenv("EXECUTE_REAL_ORDERS", "false").lower() == "true"

def get_account(name: str) -> ProductionAccount:
    """Get or create account instance with caching"""
    account_key = name.lower()
    if account_key not in accounts:
        accounts[account_key] = ProductionAccount(account_key, paper_trading=paper_trading)
    return accounts[account_key]

@mcp.tool()
async def buy_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """
    Execute buy order through Alpaca with risk management.
    
    Args:
        name: Trader account name
        symbol: Stock ticker symbol (e.g., 'AAPL')
        quantity: Number of shares to buy (must be positive)
        rationale: Reason for the trade for compliance and analysis
    
    Returns:
        String with order result and updated portfolio status
    """
    try:
        account = get_account(name)
        result = account.buy_shares(symbol.upper(), quantity, rationale)
        
        # Log for monitoring
        trading_mode = "REAL" if execute_real_orders else "SIMULATED"
        print(f"[{trading_mode}] {name} BUY {quantity} {symbol}: {result[:100]}...")
        
        return result
    
    except Exception as e:
        error_msg = f"❌ Buy order system error: {str(e)}"
        print(f"ERROR: {name} buy {symbol}: {error_msg}")
        return error_msg

@mcp.tool()
async def sell_shares(name: str, symbol: str, quantity: int, rationale: str) -> str:
    """
    Execute sell order through Alpaca with risk management.
    
    Args:
        name: Trader account name
        symbol: Stock ticker symbol (e.g., 'AAPL')
        quantity: Number of shares to sell (must be positive)
        rationale: Reason for the trade for compliance and analysis
    
    Returns:
        String with order result and updated portfolio status
    """
    try:
        account = get_account(name)
        result = account.sell_shares(symbol.upper(), quantity, rationale)
        
        # Log for monitoring
        trading_mode = "REAL" if execute_real_orders else "SIMULATED"
        print(f"[{trading_mode}] {name} SELL {quantity} {symbol}: {result[:100]}...")
        
        return result
    
    except Exception as e:
        error_msg = f"❌ Sell order system error: {str(e)}"
        print(f"ERROR: {name} sell {symbol}: {error_msg}")
        return error_msg

@mcp.tool()
async def get_account_info(name: str) -> str:
    """
    Get comprehensive account information and portfolio status.
    
    Args:
        name: Trader account name
    
    Returns:
        Detailed account report with real-time data
    """
    try:
        account = get_account(name)
        return account.get_detailed_report()
    
    except Exception as e:
        return f"❌ Error getting account info: {str(e)}"

@mcp.tool()
async def sync_account_with_broker(name: str) -> str:
    """
    Synchronize local account state with Alpaca broker account.
    Updates balance, holdings, and recent transactions.
    
    Args:
        name: Trader account name
    
    Returns:
        String with sync result status
    """
    try:
        account = get_account(name)
        result = account.sync_with_alpaca()
        print(f"SYNC: {name} - {result}")
        return result
    
    except Exception as e:
        error_msg = f"❌ Sync failed: {str(e)}"
        print(f"SYNC ERROR: {name} - {error_msg}")
        return error_msg

@mcp.tool()
async def get_portfolio_summary(name: str) -> Dict[str, Any]:
    """
    Get structured portfolio data for programmatic use.
    
    Args:
        name: Trader account name
    
    Returns:
        Dictionary with portfolio metrics and holdings
    """
    try:
        account = get_account(name)
        portfolio_value = account.calculate_portfolio_value()
        
        return {
            "account_name": name,
            "cash_balance": account.balance,
            "portfolio_value": portfolio_value,
            "total_return": portfolio_value - 10000.0,  # Assuming 10k start
            "holdings_count": len(account.holdings),
            "holdings": account.holdings,
            "last_sync": account.last_sync_time,
            "paper_trading": account.paper_trading,
            "real_orders_enabled": execute_real_orders
        }
    
    except Exception as e:
        return {"error": f"Failed to get portfolio summary: {str(e)}"}

@mcp.tool()
async def get_recent_transactions(name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent trading transactions for analysis.
    
    Args:
        name: Trader account name
        limit: Maximum number of transactions to return
    
    Returns:
        List of recent transaction dictionaries
    """
    try:
        account = get_account(name)
        recent_transactions = account.transactions[-limit:] if account.transactions else []
        
        return [
            {
                "symbol": t.symbol,
                "quantity": t.quantity,
                "price": t.price,
                "total_value": abs(t.quantity * t.price),
                "action": "BUY" if t.quantity > 0 else "SELL",
                "timestamp": t.timestamp,
                "rationale": t.rationale
            }
            for t in reversed(recent_transactions)  # Most recent first
        ]
    
    except Exception as e:
        return [{"error": f"Failed to get transactions: {str(e)}"}]

@mcp.tool()
async def get_strategy(name: str) -> str:
    """
    Get current investment strategy for the account.
    
    Args:
        name: Trader account name
    
    Returns:
        Current investment strategy description
    """
    try:
        account = get_account(name)
        return account.get_strategy()
    
    except Exception as e:
        return f"❌ Error getting strategy: {str(e)}"

@mcp.tool()
async def change_strategy(name: str, strategy: str) -> str:
    """
    Update investment strategy for the account.
    
    Args:
        name: Trader account name
        strategy: New investment strategy description
    
    Returns:
        Confirmation of strategy update
    """
    try:
        account = get_account(name)
        result = account.change_strategy(strategy)
        print(f"STRATEGY CHANGE: {name} -> {strategy[:50]}...")
        return result
    
    except Exception as e:
        return f"❌ Error changing strategy: {str(e)}"

@mcp.tool()
async def get_position_details(name: str, symbol: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific position.
    
    Args:
        name: Trader account name
        symbol: Stock ticker symbol
    
    Returns:
        Dictionary with position details and current market data
    """
    try:
        account = get_account(name)
        symbol = symbol.upper()
        
        quantity = account.holdings.get(symbol, 0)
        if quantity == 0:
            return {"symbol": symbol, "quantity": 0, "message": "No position in this symbol"}
        
        current_price = account.get_real_price(symbol)
        market_value = current_price * quantity if current_price > 0 else 0
        
        # Calculate average cost basis from transactions
        cost_basis = 0
        total_shares = 0
        for t in account.transactions:
            if t.symbol == symbol and t.quantity > 0:  # Only buy transactions
                cost_basis += t.quantity * t.price
                total_shares += t.quantity
        
        avg_cost = cost_basis / total_shares if total_shares > 0 else 0
        unrealized_pl = (current_price - avg_cost) * quantity if avg_cost > 0 else 0
        
        return {
            "symbol": symbol,
            "quantity": quantity,
            "current_price": current_price,
            "market_value": market_value,
            "average_cost": avg_cost,
            "unrealized_pl": unrealized_pl,
            "unrealized_pl_percent": (unrealized_pl / cost_basis * 100) if cost_basis > 0 else 0
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
        return {
            "paper_trading": paper_trading,
            "real_orders_enabled": execute_real_orders,
            "active_accounts": len(accounts),
            "account_names": list(accounts.keys()),
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