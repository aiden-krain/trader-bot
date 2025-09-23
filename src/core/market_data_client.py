"""
Market Data Client - Pure Alpaca market data operations.
Handles price fetching, market status, and historical data with no fallbacks.
"""

from typing import Dict, Any, List
from datetime import datetime, date

from .base_alpaca_client import BaseAlpacaClient


class MarketDataClient(BaseAlpacaClient):
    """
    Simple market data client that handles all price and market operations.
    Pure Alpaca integration - no test prices or fallbacks.
    """
    
    def __init__(self, paper_trading: bool = True, trader_name: str = None, shared_connection=None):
        super().__init__(paper_trading, trader_name, shared_connection)
    
    def get_real_price(self, symbol: str) -> float:
        """Get current real-time price for a symbol from Alpaca - no fallbacks"""
        try:
            from alpaca.data.requests import StockLatestQuoteRequest
            req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.data_client.get_stock_latest_quote(req)
            
            if symbol in quotes:
                quote = quotes[symbol]
                # Use midpoint of bid/ask for more accurate pricing
                if quote.ask_price and quote.bid_price:
                    return (float(quote.ask_price) + float(quote.bid_price)) / 2
                elif quote.ask_price:
                    return float(quote.ask_price)
                elif quote.bid_price:
                    return float(quote.bid_price)
                    
            # Fallback to latest trade
            from alpaca.data.requests import StockLatestTradeRequest
            trade_req = StockLatestTradeRequest(symbol_or_symbols=symbol)
            trades = self.data_client.get_stock_latest_trade(trade_req)
            
            if symbol in trades:
                trade = trades[symbol]
                if trade.price:
                    return float(trade.price)
            
            # If no price available, raise exception instead of returning test price
            raise ValueError(f"No price data available for {symbol}")
            
        except Exception as e:
            print(f"Error getting real-time price for {symbol}: {e}")
            raise e
    
    def get_market_status(self) -> Dict:
        """Get current market status (open/closed) from Alpaca with proper timezone handling"""
        try:
            from alpaca.trading.requests import GetCalendarRequest
            import pytz
            
            # Get today's market calendar
            today = date.today()
            request = GetCalendarRequest(start=today, end=today)
            calendar = self.trading_client.get_calendar(request)
            
            if calendar:
                market_day = calendar[0]
                
                # Convert to Eastern Time (market timezone)
                eastern = pytz.timezone('US/Eastern')
                now_et = datetime.now(eastern)
                
                # Market times are already in Eastern Time
                market_open_dt = datetime.combine(today, market_day.open.time()).replace(tzinfo=eastern)
                market_close_dt = datetime.combine(today, market_day.close.time()).replace(tzinfo=eastern)
                
                is_open = market_open_dt <= now_et <= market_close_dt
                
                return {
                    "is_open": is_open,
                    "date": str(today),
                    "market_open": str(market_day.open.time()),
                    "market_close": str(market_day.close.time()),
                    "current_time_et": str(now_et.time()),
                    "timezone": "US/Eastern"
                }
            else:
                # Market is closed (no calendar entry for today - weekend/holiday)
                return {
                    "is_open": False,
                    "date": str(today),
                    "reason": "No market session today (weekend/holiday)"
                }
                
        except Exception as e:
            print(f"Error getting market status: {e}")
            raise e
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote data for a symbol"""
        try:
            from alpaca.data.requests import StockLatestQuoteRequest
            req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.data_client.get_stock_latest_quote(req)
            
            if symbol in quotes:
                quote = quotes[symbol]
                return {
                    "symbol": symbol,
                    "bid": float(quote.bid_price) if quote.bid_price else None,
                    "ask": float(quote.ask_price) if quote.ask_price else None,
                    "bid_size": int(quote.bid_size) if quote.bid_size else None,
                    "ask_size": int(quote.ask_size) if quote.ask_size else None,
                    "timestamp": str(quote.timestamp) if quote.timestamp else None
                }
            else:
                raise ValueError(f"No quote data available for {symbol}")
                
        except Exception as e:
            print(f"Error getting quote for {symbol}: {e}")
            raise e
    
    def get_bars(self, symbol: str, timeframe: str = "1Day", limit: int = 30) -> Dict[str, Any]:
        """Get historical price bars for a symbol"""
        try:
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame
            
            # Map timeframe string to TimeFrame object
            timeframe_map = {
                "1Min": TimeFrame.Minute,
                "5Min": TimeFrame(5, "minute"),
                "15Min": TimeFrame(15, "minute"),
                "1Hour": TimeFrame.Hour,
                "1Day": TimeFrame.Day
            }
            
            tf = timeframe_map.get(timeframe, TimeFrame.Day)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                limit=limit
            )
            
            bars = self.data_client.get_stock_bars(request)
            
            if symbol in bars:
                bar_data = bars[symbol]
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "bars": [
                        {
                            "timestamp": str(bar.timestamp),
                            "open": float(bar.open),
                            "high": float(bar.high),
                            "low": float(bar.low),
                            "close": float(bar.close),
                            "volume": int(bar.volume)
                        }
                        for bar in bar_data
                    ]
                }
            else:
                raise ValueError(f"No bar data available for {symbol}")
                
        except Exception as e:
            print(f"Error getting bars for {symbol}: {e}")
            raise e
    
    def search_assets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for tradeable assets by symbol or name"""
        try:
            from alpaca.trading.requests import GetAssetsRequest
            from alpaca.trading.enums import AssetClass, AssetStatus
            
            # Search for assets
            request = GetAssetsRequest(
                status=AssetStatus.ACTIVE,
                asset_class=AssetClass.US_EQUITY
            )
            
            assets = self.trading_client.get_all_assets(request)
            
            # Filter assets that match the query
            matching_assets = []
            query_upper = query.upper()
            
            for asset in assets:
                if (query_upper in asset.symbol.upper() or 
                    (asset.name and query_upper in asset.name.upper())):
                    matching_assets.append({
                        "symbol": asset.symbol,
                        "name": asset.name or "",
                        "exchange": asset.exchange.value if asset.exchange else "",
                        "tradable": asset.tradable,
                        "marginable": asset.marginable,
                        "shortable": asset.shortable,
                        "easy_to_borrow": asset.easy_to_borrow,
                        "fractionable": asset.fractionable
                    })
                    
                    if len(matching_assets) >= limit:
                        break
            
            return matching_assets
            
        except Exception as e:
            print(f"Error searching assets for '{query}': {e}")
            raise e
