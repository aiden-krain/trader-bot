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

# Module-level tracking to prevent duplicate logging across ALL instances
_logged_traders = set()

class BaseAlpacaClient:
    """
    Base class for all Alpaca API clients with shared connection management.
    Handles authentication, connection caching, and credential management.
    All other clients inherit from this for consistent connection management.
    """
    
    # Class-level cache for shared connections
    _connection_cache = {}
    
    def __init__(self, paper_trading: bool = True, trader_name: str = None, shared_connection=None):
        self.paper_trading = paper_trading
        self.trader_name = trader_name or "Unknown"
        
        if shared_connection:
            # Use shared connection to avoid multiple API calls
            self.trading_client = shared_connection['trading_client']
            self.data_client = shared_connection['data_client']
            self.api_key = shared_connection['api_key']
            self.secret_key = shared_connection['secret_key']
            # Skip verification for shared connections to avoid duplicates
        else:
            # Create new connection
            self.api_key, self.secret_key = self._get_trader_credentials(trader_name)
            self.trading_client = TradingClient(self.api_key, self.secret_key, paper=self.paper_trading)
            self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
            
            # Verify connection only for new connections
            self._verify_connection()
    
    def _get_trader_credentials(self, trader_name: str = None) -> Tuple[str, str]:
        """Retrieve trader-specific or generic Alpaca API credentials"""
        api_key = None
        secret_key = None
        
        # Only log credential retrieval once per trader
        credential_key = f"creds_{trader_name}"
        if credential_key not in _logged_traders:
            # Try trader-specific credentials first
            if trader_name:
                print(f"🔍 Retrieving Alpaca API credentials for {trader_name}")
                trader_key = f"{trader_name.upper()}_ALPACA_KEY"
                trader_secret = f"{trader_name.upper()}_ALPACA_SECRET"
                
                api_key = os.getenv(trader_key)
                secret_key = os.getenv(trader_secret)
                
                if api_key and secret_key:
                    print(f"🔑 Using trader-specific credentials for {trader_name}")
                    _logged_traders.add(credential_key)
                    return api_key, secret_key
            
            # Fall back to generic credentials
            if not api_key or not secret_key:
                api_key = os.getenv("ALPACA_KEY")
                secret_key = os.getenv("ALPACA_SECRET")
                
                if api_key and secret_key:
                    print("🔑 Using generic Alpaca credentials")
                    _logged_traders.add(credential_key)
                    return api_key, secret_key
        else:
            # Silent retrieval for already logged traders
            if trader_name:
                trader_key = f"{trader_name.upper()}_ALPACA_KEY"
                trader_secret = f"{trader_name.upper()}_ALPACA_SECRET"
                api_key = os.getenv(trader_key)
                secret_key = os.getenv(trader_secret)
                
            if not api_key or not secret_key:
                api_key = os.getenv("ALPACA_KEY")
                secret_key = os.getenv("ALPACA_SECRET")
                
            if api_key and secret_key:
                return api_key, secret_key
        
        # If we still don't have credentials, raise an error
        raise ValueError("No Alpaca API credentials found. Please set ALPACA_KEY and ALPACA_SECRET environment variables.")
    
    def _verify_connection(self):
        """Verify API connection and log account status"""
        try:
            # Only log once per trader to prevent duplicates
            trader_key = f"{self.trader_name}_{self.paper_trading}"
            if trader_key in _logged_traders:
                return
                
            account = self.trading_client.get_account()
            env_type = "Paper" if self.paper_trading else "Live"
            print(f"✅ {self.trader_name}: Connected to Alpaca {env_type} Trading")
            print(f"   💰 Portfolio: ${float(account.portfolio_value):,.2f} | Buying Power: ${float(account.buying_power):,.2f}")
            
            # Mark this trader as logged
            _logged_traders.add(trader_key)
        except Exception as e:
            print(f"❌ Failed to connect to Alpaca for {self.trader_name}: {e}")
            raise e
