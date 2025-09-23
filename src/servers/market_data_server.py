"""
Market Data MCP Server - Focused on market data and analysis.
Provides comprehensive market information, stock analysis, and asset search using MarketDataClient.
Shared/global server that provides market data to all traders without trader-specific state.
"""

import os
import sys
import asyncio

from mcp.server.fastmcp import FastMCP
from core.alpaca_client import AlpacaClient
from dotenv import load_dotenv

# Import Pydantic models for structured responses
from models import (
    StockPrice, MarketStatus, StockBars, PerformanceAnalysis, 
    MarketMover, AssetValidation, AssetInfo, Bar
)

load_dotenv()

mcp = FastMCP("Market Data Server")

# Trading mode configuration
paper_trading = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"

# Use Warren as default trader for shared market data server
# This provides market data functionality that all traders can use
alpaca = AlpacaClient(paper_trading=paper_trading, trader_name="Warren")

@mcp.tool()
async def get_stock_price(symbol: str) -> StockPrice:
    """
    Get current stock price for a symbol using MarketDataClient.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        StockPrice model containing price, timestamp, and metadata
    """
    try:
        price = alpaca.market_data.get_real_price(symbol)
        quote = alpaca.market_data.get_quote(symbol)
        
        if price > 0:
            return StockPrice(
                symbol=symbol,
                price=price,
                bid=quote.get("bid"),
                ask=quote.get("ask"),
                spread=quote.get("ask", 0) - quote.get("bid", 0) if quote.get("ask") and quote.get("bid") else None,
                source="alpaca",
                timestamp=quote.get("timestamp") or asyncio.get_event_loop().time(),
                paper_trading=paper_trading
            )
        else:
            return StockPrice(
                symbol=symbol,
                price=0.0,
                source="alpaca",
                timestamp=asyncio.get_event_loop().time(),
                paper_trading=paper_trading
            )
    
    except Exception as e:
        return StockPrice(
            symbol=symbol,
            price=0.0,
            source="alpaca",
            timestamp=asyncio.get_event_loop().time(),
            paper_trading=paper_trading
        )

@mcp.tool()
async def get_market_status() -> MarketStatus:
    """
    Get current market status using MarketDataClient.
    
    Returns:
        MarketStatus model containing market open/close status and hours
    """
    try:
        status_data = alpaca.market_data.get_market_status()
        return MarketStatus(
            is_open=status_data.get("is_open", False),
            next_open=status_data.get("next_open"),
            next_close=status_data.get("next_close"),
            timezone=status_data.get("timezone", "America/New_York")
        )
    except Exception as e:
        return MarketStatus(
            is_open=False,
            timezone="America/New_York"
        )

@mcp.tool()
async def search_stocks(query: str, limit: int = 10) -> list[AssetInfo]:
    """
    Search for tradeable stocks by symbol or company name using MarketDataClient.
    
    Args:
        query: Search term (symbol or company name)
        limit: Maximum number of results (default 10)
    
    Returns:
        List of AssetInfo models with trading details
    """
    try:
        results = alpaca.market_data.search_assets(query, limit=limit)
        
        # Enhance results with current prices for tradeable assets
        enhanced_results = []
        for asset in results:
            if isinstance(asset, dict) and "error" not in asset and asset.get("tradable", False):
                # Add current price if available
                current_price = None
                try:
                    price = alpaca.market_data.get_real_price(asset["symbol"])
                    current_price = price if price > 0 else None
                except:
                    pass
                
                enhanced_results.append(AssetInfo(
                    symbol=asset["symbol"],
                    name=asset.get("name"),
                    exchange=asset.get("exchange"),
                    tradable=asset.get("tradable", False),
                    marginable=asset.get("marginable"),
                    shortable=asset.get("shortable"),
                    current_price=current_price,
                    paper_trading=paper_trading
                ))
        
        return enhanced_results
    
    except Exception as e:
        return []

@mcp.tool()
async def validate_symbol(symbol: str) -> AssetValidation:
    """
    Validate if a stock symbol is tradeable using MarketDataClient.
    
    Args:
        symbol: Stock ticker symbol to validate
    
    Returns:
        AssetValidation model containing validation result and asset details
    """
    try:
        # Search for exact symbol match
        assets = alpaca.market_data.search_assets(symbol, limit=1)
        
        if assets and len(assets) > 0 and "error" not in assets[0]:
            asset = assets[0]
            if asset["symbol"].upper() == symbol.upper():
                return AssetValidation(
                    symbol=symbol,
                    valid=True,
                    tradable=asset.get("tradable", False),
                    name=asset.get("name", ""),
                    exchange=asset.get("exchange", ""),
                    marginable=asset.get("marginable", False),
                    shortable=asset.get("shortable", False),
                    paper_trading=paper_trading
                )
        
        return AssetValidation(
            symbol=symbol,
            valid=False,
            paper_trading=paper_trading
        )
    
    except Exception as e:
        return AssetValidation(
            symbol=symbol,
            valid=False,
            paper_trading=paper_trading,
            error=str(e)
        )

@mcp.tool()
async def get_stock_bars(symbol: str, timeframe: str = "1Day", limit: int = 30) -> StockBars:
    """
    Get historical price bars/candles for technical analysis using MarketDataClient.
    
    Args:
        symbol: Stock ticker symbol
        timeframe: Bar timeframe ('1Min', '5Min', '15Min', '1Hour', '1Day')
        limit: Number of bars to retrieve (default 30)
    
    Returns:
        StockBars model containing historical OHLCV data
    """
    try:
        bars_data = alpaca.market_data.get_bars(symbol, timeframe, limit=limit)
        
        if "error" in bars_data:
            return StockBars(
                symbol=symbol,
                timeframe=timeframe,
                bars=[],
                paper_trading=paper_trading
            )
        
        bars = []
        for bar_data in bars_data.get("bars", []):
            bars.append(Bar(
                timestamp=bar_data["timestamp"],
                open=bar_data["open"],
                high=bar_data["high"],
                low=bar_data["low"],
                close=bar_data["close"],
                volume=bar_data["volume"]
            ))
        
        return StockBars(
            symbol=symbol,
            timeframe=timeframe,
            bars=bars,
            paper_trading=paper_trading
        )
    
    except Exception as e:
        return StockBars(
            symbol=symbol,
            timeframe=timeframe,
            bars=[],
            paper_trading=paper_trading
        )

@mcp.tool()
async def analyze_stock_performance(symbol: str, days: int = 30) -> PerformanceAnalysis:
    """
    Analyze stock performance over specified period using MarketDataClient.
    
    Args:
        symbol: Stock ticker symbol
        days: Number of days to analyze (default 30)
    
    Returns:
        PerformanceAnalysis model containing performance metrics and analysis
    """
    try:
        # Get historical data using MarketDataClient
        bars_data = alpaca.market_data.get_bars(symbol, "1Day", limit=days)
        
        if "error" in bars_data:
            return PerformanceAnalysis(
                symbol=symbol,
                period_days=0,
                first_price=0.0,
                last_price=0.0,
                high_price=0.0,
                low_price=0.0,
                total_return_percent=0.0,
                price_range_percent=0.0,
                average_volume=0,
                paper_trading=paper_trading,
                analysis_timestamp=asyncio.get_event_loop().time()
            )
        
        bars = bars_data.get("bars", [])
        if len(bars) < 2:
            return PerformanceAnalysis(
                symbol=symbol,
                period_days=len(bars),
                first_price=0.0,
                last_price=0.0,
                high_price=0.0,
                low_price=0.0,
                total_return_percent=0.0,
                price_range_percent=0.0,
                average_volume=0,
                paper_trading=paper_trading,
                analysis_timestamp=asyncio.get_event_loop().time()
            )
        
        # Calculate performance metrics
        first_price = bars[0]["close"]
        last_price = bars[-1]["close"]
        high_price = max(bar["high"] for bar in bars)
        low_price = min(bar["low"] for bar in bars)
        
        total_return = ((last_price - first_price) / first_price) * 100
        
        # Calculate average volume
        avg_volume = sum(bar["volume"] for bar in bars) / len(bars)
        
        return PerformanceAnalysis(
            symbol=symbol,
            period_days=len(bars),
            first_price=first_price,
            last_price=last_price,
            high_price=high_price,
            low_price=low_price,
            total_return_percent=round(total_return, 2),
            price_range_percent=round(((high_price - low_price) / first_price) * 100, 2),
            average_volume=int(avg_volume),
            paper_trading=paper_trading,
            analysis_timestamp=asyncio.get_event_loop().time()
        )
    
    except Exception as e:
        return PerformanceAnalysis(
            symbol=symbol,
            period_days=0,
            first_price=0.0,
            last_price=0.0,
            high_price=0.0,
            low_price=0.0,
            total_return_percent=0.0,
            price_range_percent=0.0,
            average_volume=0,
            paper_trading=paper_trading,
            analysis_timestamp=asyncio.get_event_loop().time()
        )

@mcp.tool()
async def get_market_movers(direction: str = "gainers", limit: int = 10) -> list[MarketMover]:
    """
    Get top market movers (gainers or losers) using MarketDataClient.
    Note: This is a simplified implementation as Alpaca doesn't provide direct screener API.
    
    Args:
        direction: "gainers" or "losers"
        limit: Number of stocks to return
    
    Returns:
        List of MarketMover models with top performing stocks
    """
    try:
        # This is a simplified implementation
        # In practice, you'd need a separate market data provider or screener service
        popular_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA", "META", "NFLX", "SPY", "QQQ"]
        
        movers = []
        for symbol in popular_symbols[:limit]:
            try:
                bars_data = alpaca.market_data.get_bars(symbol, "1Day", limit=2)
                bars = bars_data.get("bars", [])
                
                if len(bars) >= 2:
                    prev_close = bars[-2]["close"]
                    current_close = bars[-1]["close"]
                    change_percent = ((current_close - prev_close) / prev_close) * 100
                    
                    movers.append(MarketMover(
                        symbol=symbol,
                        current_price=current_close,
                        previous_close=prev_close,
                        change_percent=round(change_percent, 2),
                        change_dollar=round(current_close - prev_close, 2),
                        paper_trading=paper_trading
                    ))
            except:
                continue
        
        # Sort by change percentage
        if direction == "gainers":
            movers.sort(key=lambda x: x.change_percent, reverse=True)
        else:
            movers.sort(key=lambda x: x.change_percent)
        
        return movers[:limit]
    
    except Exception as e:
        return []

# Resource endpoints for market data
@mcp.resource("market://status")
async def read_market_status_resource() -> str:
    """Get market status as resource"""
    try:
        status_data = alpaca.market_data.get_market_status()
        return f"Market Status: {'Open' if status_data.get('is_open', False) else 'Closed'}"
    except Exception as e:
        return f"❌ Error loading market status: {str(e)}"

@mcp.resource("market://price/{symbol}")
async def read_stock_price_resource(symbol: str) -> str:
    """Get stock price as resource"""
    try:
        price = alpaca.market_data.get_real_price(symbol)
        return f"{symbol}: ${price:.2f}"
    except Exception as e:
        return f"❌ Error loading price for {symbol}: {str(e)}"

if __name__ == "__main__":
    print(f"🚀 Starting Market Data MCP Server")
    print(f"   Paper Trading: {paper_trading}")
    print(f"   Focus: Market Data & Analysis")
    
    mcp.run(transport="stdio")
