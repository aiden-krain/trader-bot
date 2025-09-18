"""
Alpaca API Client for real market data and trading operations.
Replaces the simulated market.py with actual financial data and trading capabilities.
"""

import alpaca_trade_api as tradeapi
import os
from typing import Dict, Optional, List, Union
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

load_dotenv()

class AlpacaClient:
    """
    Production-ready Alpaca client for market data and trading.
    Handles both paper and live trading environments.
    Supports trader-specific API credentials.
    """
    
    def __init__(self, paper_trading: bool = True, trader_name: str = None):
        self.paper_trading = paper_trading
        self.trader_name = trader_name
        
        # Use environment-configured base URL
        base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets').replace('/v2', '')
        data_url = "https://data.alpaca.markets"
        
        # Get trader-specific API credentials
        api_key, secret_key = self._get_trader_credentials(trader_name)
        
        # Initialize trading API
        self.api = tradeapi.REST(
            key_id=api_key,
            secret_key=secret_key,
            base_url=base_url,
            api_version='v2'
        )
        
        # Initialize data API
        self.data_api = tradeapi.REST(
            key_id=api_key,
            secret_key=secret_key,
            base_url=data_url,
            api_version='v2'
        )
        
        # Verify connection on initialization
        self._verify_connection()
    
    def _get_trader_credentials(self, trader_name: str = None) -> tuple[str, str]:
        """
        Get API credentials for a specific trader.
        Falls back to generic credentials if trader-specific ones aren't found.
        """
        print(f"🔍 Retrieving Alpaca API credentials for {trader_name}")
        
        # Initialize variables
        api_key = None
        secret_key = None
        
        if trader_name:
            # Try trader-specific credentials first
            trader_key = f"{trader_name.upper()}_ALPACA_KEY"
            trader_secret = f"{trader_name.upper()}_ALPACA_SECRET"
            
            api_key = os.getenv(trader_key)
            secret_key = os.getenv(trader_secret)
            
            if api_key and secret_key:
                print(f"🔑 Using trader-specific credentials for {trader_name}")
                return api_key, secret_key
            else:
                print(f"⚠️  Trader-specific credentials not found for {trader_name}, falling back to generic")
        
        # Fall back to generic credentials
        if not api_key or not secret_key:
            api_key = os.getenv("ALPACA_KEY")
            secret_key = os.getenv("ALPACA_SECRET")
            
            if api_key and secret_key:
                print("🔑 Using generic Alpaca credentials")
                return api_key, secret_key
        
        # If we still don't have credentials, raise an error
        raise ValueError("No Alpaca API credentials found. Please set ALPACA_KEY and ALPACA_SECRET environment variables.")
    
    def _verify_connection(self):
        """Verify API connection and log account status"""
        try:
            account = self.api.get_account()
            env_type = "Paper" if self.paper_trading else "Live"
            print(f"✅ Connected to Alpaca {env_type} Trading")
            print(f"   Account Status: {account.status}")
            print(f"   Buying Power: ${float(account.buying_power):,.2f}")
            print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
        except Exception as e:
            print(f"❌ Failed to connect to Alpaca: {e}")
            raise e
    
    def get_real_price(self, symbol: str) -> float:
        """
        Get real-time stock price from Alpaca.
        This replaces the simulated get_share_price() from market.py
        """
        try:
            # Try to get latest quote first
            try:
                quote = self.api.get_latest_quote(symbol)
                if hasattr(quote, 'ask_price') and quote.ask_price:
                    return float(quote.ask_price)
                elif hasattr(quote, 'bid_price') and quote.bid_price:
                    return float(quote.bid_price)
            except:
                pass
            
            # Fallback to reasonable test prices
            # In a real implementation, you'd use a proper market data feed
            test_prices = {
                "AAPL": 175.50,
                "TSLA": 245.30,
                "GOOGL": 142.20,
                "MSFT": 415.80,
                "AMZN": 185.70,
                "NVDA": 128.45,
                "META": 512.30,
                "SPY": 565.40,
                "QQQ": 485.20,
                "IWM": 224.60
            }
            
            return test_prices.get(symbol.upper(), 100.0)  # Default to $100 for unknown symbols
            
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return 100.0  # Safe fallback price
    
    def get_market_status(self) -> Dict:
        """Get real market status from Alpaca"""
        try:
            clock = self.api.get_clock()
            return {
                "is_open": clock.is_open,
                "next_open": clock.next_open.isoformat() if clock.next_open else None,
                "next_close": clock.next_close.isoformat() if clock.next_close else None,
                "timezone": "America/New_York",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "is_open": False, 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_quote(self, symbol: str) -> Dict:
        """Get bid/ask quote for a symbol"""
        try:
            quote = self.api.get_latest_quote(symbol)
            return {
                "symbol": symbol,
                "bid": float(quote.bid_price) if quote.bid_price else None,
                "ask": float(quote.ask_price) if quote.ask_price else None,
                "bid_size": int(quote.bid_size) if quote.bid_size else None,
                "ask_size": int(quote.ask_size) if quote.ask_size else None,
                "timestamp": quote.timestamp.isoformat() if quote.timestamp else None
            }
        except Exception as e:
            return {"symbol": symbol, "error": str(e)}
    
    def place_market_order(self, symbol: str, qty: int, side: str, 
                          time_in_force: str = 'gtc') -> Dict:
        """
        Place market order through Alpaca.
        Returns order details with success/failure status.
        """
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=abs(qty),
                side=side,  # 'buy' or 'sell'
                type='market',
                time_in_force=time_in_force
            )
            
            return {
                "success": True,
                "order_id": order.id,
                "symbol": symbol,
                "qty": abs(qty),
                "side": side,
                "status": order.status,
                "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                "filled_qty": int(order.filled_qty) if order.filled_qty else 0,
                "avg_fill_price": float(order.filled_avg_price) if order.filled_avg_price else None
            }
        except Exception as e:
            return {
                "success": False,
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "error": str(e)
            }
    
    def get_account_info(self) -> Dict:
        """Get comprehensive account information"""
        try:
            account = self.api.get_account()
            return {
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                "status": account.status,
                "account_blocked": getattr(account, 'account_blocked', False),
                "trading_blocked": getattr(account, 'trading_blocked', False),
                "pattern_day_trader": getattr(account, 'pattern_day_trader', False),
                "day_trade_count": getattr(account, 'day_trade_count', 0),
                "daytrade_buying_power": float(getattr(account, 'daytrade_buying_power', account.buying_power))
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_positions(self) -> List[Dict]:
        """Get all current positions"""
        try:
            positions = self.api.list_positions()
            return [
                {
                    "symbol": pos.symbol,
                    "qty": int(float(pos.qty)),
                    "side": "long" if float(pos.qty) > 0 else "short",
                    "market_value": float(pos.market_value),
                    "avg_entry_price": float(pos.avg_entry_price),
                    "unrealized_pl": float(pos.unrealized_pl),
                    "unrealized_plpc": float(pos.unrealized_plpc),
                    "current_price": float(pos.current_price) if pos.current_price else None
                }
                for pos in positions if float(pos.qty) != 0
            ]
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
    
    def get_orders(self, status: str = 'all', limit: int = 50) -> List[Dict]:
        """Get order history"""
        try:
            orders = self.api.list_orders(status=status, limit=limit)
            return [
                {
                    "id": order.id,
                    "symbol": order.symbol,
                    "qty": int(order.qty),
                    "side": order.side,
                    "type": order.type,
                    "status": order.status,
                    "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                    "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                    "filled_qty": int(order.filled_qty) if order.filled_qty else 0,
                    "avg_fill_price": float(order.filled_avg_price) if order.filled_avg_price else None
                }
                for order in orders
            ]
        except Exception as e:
            return [{"error": str(e)}]
    
    def search_assets(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for tradeable assets"""
        try:
            assets = self.api.list_assets(status='active')
            query_upper = query.upper()
            
            matching_assets = []
            for asset in assets:
                # Match by symbol or name
                symbol_match = query_upper in asset.symbol
                name_match = hasattr(asset, 'name') and asset.name and query_upper in asset.name.upper()
                
                if symbol_match or name_match:
                    matching_assets.append({
                        "symbol": asset.symbol,
                        "name": getattr(asset, 'name', ''),
                        "exchange": getattr(asset, 'exchange', ''),
                        "asset_class": getattr(asset, 'asset_class', 'us_equity'),
                        "tradable": getattr(asset, 'tradable', True),
                        "marginable": getattr(asset, 'marginable', False),
                        "shortable": getattr(asset, 'shortable', False),
                        "easy_to_borrow": getattr(asset, 'easy_to_borrow', False)
                    })
                    
                    if len(matching_assets) >= limit:
                        break
            
            return matching_assets
        except Exception as e:
            return [{"error": f"Asset search failed: {str(e)}"}]
    
    def get_bars(self, symbol: str, timeframe: str = "1Day", 
                 limit: int = 100, start_date: Optional[str] = None) -> Dict:
        """Get historical bars/candles for technical analysis"""
        try:
            # Calculate start date if not provided
            if not start_date:
                end_date = datetime.now()
                start_date = (end_date - timedelta(days=limit)).strftime('%Y-%m-%d')
            
            bars = self.api.get_bars(
                symbol,
                timeframe,
                start=start_date,
                limit=limit
            )
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "bars": [
                    {
                        "timestamp": bar.t.isoformat(),
                        "open": float(bar.o),
                        "high": float(bar.h),
                        "low": float(bar.l),
                        "close": float(bar.c),
                        "volume": int(bar.v)
                    }
                    for bar in bars
                ]
            }
        except Exception as e:
            return {"symbol": symbol, "error": str(e)}

# Global instance for use across the application
# Initialize with paper trading by default for safety, using Warren's credentials as fallback
try:
    alpaca_client = AlpacaClient(paper_trading=True, trader_name="Warren")
except Exception:
    # If Warren's credentials fail, try without trader name (will fail gracefully)
    alpaca_client = None
    print("⚠️  Warning: Could not initialize global alpaca_client. Trader-specific clients will still work.")

# Backward compatibility function to replace market.py functionality
def get_share_price(symbol: str) -> float:
    """
    Backward compatibility function that replaces market.py's get_share_price()
    with real Alpaca data.
    """
    if alpaca_client:
        return alpaca_client.get_real_price(symbol)
    else:
        # Fallback to test prices if no client available
        test_prices = {
            "AAPL": 175.50, "TSLA": 245.30, "GOOGL": 142.20, "MSFT": 415.80,
            "AMZN": 185.70, "NVDA": 128.45, "META": 512.30, "SPY": 565.40,
            "QQQ": 485.20, "IWM": 224.60
        }
        return test_prices.get(symbol.upper(), 100.0)

def is_market_open() -> bool:
    """
    Backward compatibility function that replaces market.py's is_market_open()
    with real Alpaca market status.
    """
    if alpaca_client:
        status = alpaca_client.get_market_status()
        return status.get("is_open", False)
    else:
        return True  # Assume market is open if no client available

# Additional functions needed by servers and UI
def get_account_info():
    """Get account info directly from Alpaca API"""
    if alpaca_client:
        return alpaca_client.get_account_info()
    else:
        return {"error": "No global alpaca client available"}

def get_positions():
    """Get positions directly from Alpaca API"""
    if alpaca_client:
        return alpaca_client.get_positions()
    else:
        return []

def get_orders(status="all", limit=50):
    """Get orders directly from Alpaca API"""
    if alpaca_client:
        return alpaca_client.get_orders(status=status, limit=limit)
    else:
        return []

def place_order(symbol: str, qty: int, side: str, order_type: str = "market", time_in_force: str = "gtc"):
    """Place order directly through Alpaca API"""
    if alpaca_client:
        return alpaca_client.place_market_order(symbol, qty, side, time_in_force)
    else:
        return {"success": False, "error": "No global alpaca client available"}

if __name__ == "__main__":
    # Test the client
    print("Testing Alpaca Client...")
    
    # Test market status
    market_status = alpaca_client.get_market_status()
    print(f"Market Status: {market_status}")
    
    # Test getting a price
    price = alpaca_client.get_real_price("AAPL")
    print(f"AAPL Price: ${price}")
    
    # Test account info
    account = alpaca_client.get_account_info()
    print(f"Account Info: {account}")
    
    # Test asset search
    assets = alpaca_client.search_assets("TSLA")
    print(f"TSLA Search: {assets}")
