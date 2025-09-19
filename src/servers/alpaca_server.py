"""
Alpaca MCP Server - Provides market data and trading tools via Model Context Protocol.
This replaces the simulated market_server.py with real Alpaca financial data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from core.alpaca_client import AlpacaClient
from typing import Dict, Any, List
import asyncio
import json

mcp = FastMCP("Alpaca Market Data & Trading")

# Initialize Alpaca client
# Paper trading by default for safety - can be changed via environment variable
import os
paper_trading = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"

# Use Warren as default trader for shared market data server
# This provides market data functionality that all traders can use
alpaca = AlpacaClient(paper_trading=paper_trading, trader_name="Warren")

@mcp.tool()
async def get_stock_price(symbol: str) -> Dict[str, Any]:
    """
    Get current stock price for a symbol from Alpaca.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dict containing price, timestamp, and metadata
    """
    try:
        price = alpaca.get_real_price(symbol)
        quote = alpaca.get_quote(symbol)
        
        if price > 0:
            return {
                "symbol": symbol,
                "price": price,
                "bid": quote.get("bid"),
                "ask": quote.get("ask"),
                "spread": quote.get("ask", 0) - quote.get("bid", 0) if quote.get("ask") and quote.get("bid") else None,
                "source": "alpaca",
                "timestamp": quote.get("timestamp") or asyncio.get_event_loop().time(),
                "paper_trading": paper_trading
            }
        else:
            return {"error": f"Could not get price for {symbol}"}
    
    except Exception as e:
        return {"error": f"Failed to get price for {symbol}: {str(e)}"}

@mcp.tool()
async def get_market_status() -> Dict[str, Any]:
    """
    Get current market status from Alpaca.
    
    Returns:
        Dict containing market open/close status and hours
    """
    return alpaca.get_market_status()

@mcp.tool()
async def get_market_account_info() -> Dict[str, Any]:
    """
    Get Alpaca market account information including buying power and portfolio value.
    
    Returns:
        Dict containing market account details and trading status
    """
    account_info = alpaca.get_account_info()
    account_info["paper_trading"] = paper_trading
    return account_info

@mcp.tool()
async def get_positions() -> List[Dict[str, Any]]:
    """
    Get current positions from Alpaca account.
    
    Returns:
        List of position dictionaries with holdings and P&L
    """
    positions = alpaca.get_positions()
    # Add metadata to each position
    for pos in positions:
        pos["paper_trading"] = paper_trading
    return positions

@mcp.tool()
async def get_recent_orders(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get recent order history from Alpaca.
    
    Args:
        limit: Maximum number of orders to return (default 20)
    
    Returns:
        List of recent orders with status and fill details
    """
    orders = alpaca.get_orders(status='all', limit=limit)
    # Add metadata to each order
    for order in orders:
        if isinstance(order, dict) and "error" not in order:
            order["paper_trading"] = paper_trading
    return orders

@mcp.tool()
async def search_stocks(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for tradeable stocks by symbol or company name.
    
    Args:
        query: Search term (symbol or company name)
        limit: Maximum number of results (default 10)
    
    Returns:
        List of matching stocks with trading details
    """
    try:
        results = alpaca.search_assets(query, limit=limit)
        
        # Enhance results with current prices for tradeable assets
        enhanced_results = []
        for asset in results:
            if isinstance(asset, dict) and "error" not in asset and asset.get("tradable", False):
                # Add current price if available
                try:
                    current_price = alpaca.get_real_price(asset["symbol"])
                    asset["current_price"] = current_price if current_price > 0 else None
                except:
                    asset["current_price"] = None
                
                asset["paper_trading"] = paper_trading
                enhanced_results.append(asset)
        
        return enhanced_results
    
    except Exception as e:
        return [{"error": f"Stock search failed: {str(e)}"}]

@mcp.tool()
async def get_stock_bars(symbol: str, timeframe: str = "1Day", limit: int = 30) -> Dict[str, Any]:
    """
    Get historical price bars/candles for technical analysis.
    
    Args:
        symbol: Stock ticker symbol
        timeframe: Bar timeframe ('1Min', '5Min', '15Min', '1Hour', '1Day')
        limit: Number of bars to retrieve (default 30)
    
    Returns:
        Dict containing historical OHLCV data
    """
    try:
        bars_data = alpaca.get_bars(symbol, timeframe, limit=limit)
        bars_data["paper_trading"] = paper_trading
        return bars_data
    
    except Exception as e:
        return {"symbol": symbol, "error": f"Failed to get bars: {str(e)}"}

@mcp.tool()
async def analyze_stock_performance(symbol: str, days: int = 30) -> Dict[str, Any]:
    """
    Analyze stock performance over specified period.
    
    Args:
        symbol: Stock ticker symbol
        days: Number of days to analyze (default 30)
    
    Returns:
        Dict containing performance metrics and analysis
    """
    try:
        # Get historical data
        bars_data = alpaca.get_bars(symbol, "1Day", limit=days)
        
        if "error" in bars_data:
            return bars_data
        
        bars = bars_data.get("bars", [])
        if len(bars) < 2:
            return {"symbol": symbol, "error": "Insufficient historical data"}
        
        # Calculate performance metrics
        first_price = bars[0]["close"]
        last_price = bars[-1]["close"]
        high_price = max(bar["high"] for bar in bars)
        low_price = min(bar["low"] for bar in bars)
        
        total_return = ((last_price - first_price) / first_price) * 100
        volatility = 0  # Simplified - would need proper volatility calculation
        
        # Calculate average volume
        avg_volume = sum(bar["volume"] for bar in bars) / len(bars)
        
        return {
            "symbol": symbol,
            "period_days": len(bars),
            "first_price": first_price,
            "last_price": last_price,
            "high_price": high_price,
            "low_price": low_price,
            "total_return_percent": round(total_return, 2),
            "price_range_percent": round(((high_price - low_price) / first_price) * 100, 2),
            "average_volume": int(avg_volume),
            "paper_trading": paper_trading,
            "analysis_timestamp": asyncio.get_event_loop().time()
        }
    
    except Exception as e:
        return {"symbol": symbol, "error": f"Performance analysis failed: {str(e)}"}

@mcp.tool()
async def get_market_movers(direction: str = "gainers", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get top market movers (gainers or losers).
    Note: This is a simplified implementation as Alpaca doesn't provide direct screener API.
    
    Args:
        direction: "gainers" or "losers"
        limit: Number of stocks to return
    
    Returns:
        List of top performing stocks (limited functionality with Alpaca free tier)
    """
    try:
        # This is a simplified implementation
        # In practice, you'd need a separate market data provider or screener service
        popular_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA", "META", "NFLX", "SPY", "QQQ"]
        
        movers = []
        for symbol in popular_symbols[:limit]:
            try:
                bars_data = alpaca.get_bars(symbol, "1Day", limit=2)
                bars = bars_data.get("bars", [])
                
                if len(bars) >= 2:
                    prev_close = bars[-2]["close"]
                    current_close = bars[-1]["close"]
                    change_percent = ((current_close - prev_close) / prev_close) * 100
                    
                    movers.append({
                        "symbol": symbol,
                        "current_price": current_close,
                        "previous_close": prev_close,
                        "change_percent": round(change_percent, 2),
                        "change_dollar": round(current_close - prev_close, 2)
                    })
            except:
                continue
        
        # Sort by change percentage
        if direction == "gainers":
            movers.sort(key=lambda x: x["change_percent"], reverse=True)
        else:
            movers.sort(key=lambda x: x["change_percent"])
        
        # Add metadata
        for mover in movers:
            mover["paper_trading"] = paper_trading
        
        return movers[:limit]
    
    except Exception as e:
        return [{"error": f"Market movers query failed: {str(e)}"}]

@mcp.tool()
async def validate_symbol(symbol: str) -> Dict[str, Any]:
    """
    Validate if a stock symbol is tradeable on Alpaca.
    
    Args:
        symbol: Stock ticker symbol to validate
    
    Returns:
        Dict containing validation result and asset details
    """
    try:
        # Search for exact symbol match
        assets = alpaca.search_assets(symbol, limit=1)
        
        if assets and len(assets) > 0 and "error" not in assets[0]:
            asset = assets[0]
            if asset["symbol"].upper() == symbol.upper():
                return {
                    "symbol": symbol,
                    "valid": True,
                    "tradable": asset.get("tradable", False),
                    "name": asset.get("name", ""),
                    "exchange": asset.get("exchange", ""),
                    "marginable": asset.get("marginable", False),
                    "shortable": asset.get("shortable", False),
                    "paper_trading": paper_trading
                }
        
        return {
            "symbol": symbol,
            "valid": False,
            "paper_trading": paper_trading
        }
    
    except Exception as e:
        return {
            "symbol": symbol,
            "valid": False,
            "error": str(e),
            "paper_trading": paper_trading
        }

if __name__ == "__main__":
    print(f"Starting Alpaca MCP Server ({'Paper Trading' if paper_trading else 'Live Trading'})")
    mcp.run(transport="stdio")