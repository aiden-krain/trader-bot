"""
Simple Base Alpaca Client - Foundation for all trading operations.
Handles only connection logic and credential management.
"""

import os
from typing import Tuple
from dotenv import load_dotenv

# Modern alpaca-py imports
from alpaca.trading.client import TradingClient
from alpaca.data.historical.stock import StockHistoricalDataClient

load_dotenv()


class BaseAlpacaClient:
    """
    Simple base client that handles connection logic and credentials.
    All other clients inherit from this for consistent connection management.
    """
    
    # Class-level cache for shared connections
    _connection_cache = {}
    
    def __init__(self, paper_trading: bool = True, trader_name: str = None, shared_connection=None):
        self.paper_trading = paper_trading
        self.trader_name = trader_name or "Unknown"
        
        # Use shared connection if provided, otherwise create new one
        if shared_connection:
            self.trading_client = shared_connection['trading_client']
            self.data_client = shared_connection['data_client']
            self.api_key = shared_connection['api_key']
            self.secret_key = shared_connection['secret_key']
        else:
            # Check cache first
            cache_key = f"{trader_name}_{paper_trading}"
            if cache_key in self._connection_cache:
                cached = self._connection_cache[cache_key]
                self.trading_client = cached['trading_client']
                self.data_client = cached['data_client']
                self.api_key = cached['api_key']
                self.secret_key = cached['secret_key']
            else:
                # Create new connection
                api_key, secret_key = self._get_trader_credentials(trader_name)
                
                # Initialize modern alpaca-py clients
                self.trading_client = TradingClient(
                    api_key=api_key,
                    secret_key=secret_key,
                    paper=paper_trading
                )
                
                self.data_client = StockHistoricalDataClient(api_key, secret_key)
                
                # Store credentials for compatibility
                self.api_key = api_key
                self.secret_key = secret_key
                
                # Cache the connection
                self._connection_cache[cache_key] = {
                    'trading_client': self.trading_client,
                    'data_client': self.data_client,
                    'api_key': api_key,
                    'secret_key': secret_key
                }
                
                # Verify connection only once per trader
                self._verify_connection()
    
    def _get_trader_credentials(self, trader_name: str = None) -> Tuple[str, str]:
        """Retrieve trader-specific or generic Alpaca API credentials"""
        api_key = None
        secret_key = None
        
        # Try trader-specific credentials first
        if trader_name:
            print(f"🔍 Retrieving Alpaca API credentials for {trader_name}")
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
            account = self.trading_client.get_account()
            env_type = "Paper" if self.paper_trading else "Live"
            print(f"✅ {self.trader_name}: Connected to Alpaca {env_type} Trading")
            print(f"   💰 Portfolio: ${float(account.portfolio_value):,.2f} | Buying Power: ${float(account.buying_power):,.2f}")
        except Exception as e:
            print(f"❌ Failed to connect to Alpaca for {self.trader_name}: {e}")
            raise e
