"""
Enhanced Alpaca API Client with Risk Management Integration.
Production-ready client for real market data and trading operations with built-in risk controls.
Consolidates all trading functionality in a single, clean interface.
"""

import os
import sys
import time
import json
from typing import Dict, Any, List, Tuple, Optional, Union
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Modern alpaca-py imports
from alpaca.trading.client import TradingClient
from alpaca.data.historical.stock import StockHistoricalDataClient

# Add utils path for database operations
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import write_log

# Import decomposed clients
from core.market_data_client import MarketDataClient
from core.account_client import AccountClient
from core.trading_client import TradingClient

# Import strategy system
from strategies import create_strategy, list_strategies

load_dotenv()


class AlpacaClient:
    """
    Enhanced Alpaca client with integrated risk management and trading operations.
    Now uses decomposed architecture with specialized clients for better maintainability.
    Maintains full backward compatibility with existing code.
    """
    
    def __init__(self, paper_trading: bool = True, trader_name: str = None):
        self.paper_trading = paper_trading
        self.trader_name = trader_name or "Unknown"
        
        # Create the first client which will establish and cache the connection
        self.market_data = MarketDataClient(paper_trading, trader_name)
        
        # Share the connection with other clients to avoid multiple connections
        shared_connection = {
            'trading_client': self.market_data.trading_client,
            'data_client': self.market_data.data_client,
            'api_key': self.market_data.api_key,
            'secret_key': self.market_data.secret_key
        }
        
        self.account = AccountClient(paper_trading, trader_name, shared_connection)
        self.trading = TradingClient(paper_trading, trader_name, None, shared_connection)
        
        # Maintain existing attributes for backward compatibility
        self.trading_client = self.market_data.trading_client
        self.data_client = self.market_data.data_client
        self.risk_manager = self.trading.risk_manager
        self.api_key = self.market_data.api_key
        self.secret_key = self.market_data.secret_key
        
        # Display risk limits summary
        self._display_risk_summary()
    
    def _display_risk_summary(self):
        """Display a clean summary of risk limits for this trader"""
        # Import the module-level tracker from base client
        from core.base_alpaca_client import _logged_traders
        
        risk_key = f"risk_{self.trader_name}_{self.paper_trading}"
        if risk_key not in _logged_traders:
            risk_summary = self.risk_manager.get_risk_summary()
            print(f"   🛡️  Risk Limits: Max Position {risk_summary['max_position_size']} | Portfolio Risk {risk_summary['max_portfolio_risk']} | Daily Trades {risk_summary['max_daily_trades']}")
            _logged_traders.add(risk_key)
    
    # =============================================================================
    # MARKET DATA METHODS
    # =============================================================================
    
    def get_real_price(self, symbol: str) -> float:
        """Get current real-time price for a symbol - pure Alpaca integration"""
        return self.market_data.get_real_price(symbol)
    
    def get_market_status(self) -> Dict:
        """Get current market status (open/closed)"""
        return self.market_data.get_market_status()
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote data for a symbol"""
        return self.market_data.get_quote(symbol)
    
    def get_bars(self, symbol: str, timeframe: str = "1Day", limit: int = 30) -> Dict[str, Any]:
        """Get historical price bars for a symbol"""
        return self.market_data.get_bars(symbol, timeframe, limit)
    
    def search_assets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for tradeable assets by symbol or name"""
        return self.market_data.search_assets(query, limit)
    
    # =============================================================================
    # ACCOUNT & PORTFOLIO METHODS  
    # =============================================================================
    
    def get_account_info(self) -> Dict:
        """Get comprehensive account information"""
        return self.account.get_account_info()
    
    def get_positions(self) -> List[Dict]:
        """Get all current positions"""
        return self.account.get_positions()
    
    def calculate_portfolio_value(self) -> float:
        """Calculate current portfolio value using real Alpaca data"""
        return self.account.calculate_portfolio_value()
    
    def get_orders(self, status: str = "all", limit: int = 50) -> List[Dict]:
        """Get order history from Alpaca"""
        return self.account.get_orders(status, limit)
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary with positions and account data"""
        return self.account.get_portfolio_summary()
    
    def get_portfolio_report(self) -> str:
        """Get detailed portfolio report"""
        return self.account.get_portfolio_report()
    
    # =============================================================================
    # STRATEGY MANAGEMENT METHODS
    # =============================================================================
    
    def _get_strategy_risk_limits(self) -> dict:
        """Get risk limits from the strategy for this trader"""
        return self.trading._get_strategy_risk_limits()
    
    def get_strategy(self) -> str:
        """Get investment strategy for this trader"""
        try:
            strategy_obj = create_strategy(self.trader_name)
            return strategy_obj.get_instructions()
        except Exception as e:
            error_msg = f"❌ Strategy retrieval error: {str(e)}"
            write_log(self.trader_name, "error", error_msg)
            return error_msg
    
    def get_risk_summary(self) -> Dict[str, str]:
        """Get a summary of current risk limits from the RiskManager"""
        return self.risk_manager.get_risk_summary()
    
    def assess_trade_risk(self, symbol: str, quantity: int, conviction_level: int = 5) -> Dict[str, Any]:
        """Pre-trade risk assessment with scoring and recommendations"""
        return self.trading.assess_trade_risk(symbol, quantity, conviction_level)
    
    
    # =============================================================================
    # TRADING METHODS WITH RISK MANAGEMENT
    # =============================================================================
    
    def place_market_order(self, symbol: str, qty: int, side: str) -> Dict:
        """Place market order using modern alpaca-py"""
        return self.trading.place_market_order(symbol, qty, side)
    
    def buy_shares_with_risk_management(self, symbol: str, quantity: int, rationale: str, conviction_level: int = 5) -> str:
        """Execute buy order with enhanced risk management and logging"""
        return self.trading.buy_shares_with_risk_management(symbol, quantity, rationale, conviction_level)
    
    def sell_shares_with_risk_management(self, symbol: str, quantity: int, rationale: str, conviction_level: int = 5) -> str:
        """Execute sell order with enhanced risk management and logging"""
        return self.trading.sell_shares_with_risk_management(symbol, quantity, rationale, conviction_level)
    
    # =============================================================================
    # REPORTING & GUIDANCE METHODS
    # =============================================================================
    
    def get_trading_guidance(self) -> str:
        """Get trading guidance with current account status and risk limits"""
        try:
            account_info = self.get_account_info()
            positions = self.get_positions()
            risk_summary = self.risk_manager.get_risk_summary()
            
            guidance = f"""🎯 TRADING GUIDANCE - {self.trader_name.upper()}
 Portfolio Value: ${float(account_info.get('portfolio_value', 0)):,.2f}
💪 Available for Trading: ${float(account_info.get('buying_power', 0)):,.2f}

🛡️ RISK LIMITS:
• Max Position Size: {risk_summary['max_position_size']}
• Max Portfolio Risk: {risk_summary['max_portfolio_risk']}
• Max Daily Trades: {risk_summary['max_daily_trades']}

📊 CURRENT POSITIONS ({len(positions)}):"""
            
            if positions:
                for pos in positions:
                    pnl = float(pos.get('unrealized_pl', 0))
                    pnl_pct = float(pos.get('unrealized_plpc', 0)) * 100
                    pnl_indicator = "🟢" if pnl >= 0 else "🔴"
                    guidance += f"\\n  {pnl_indicator} {pos['symbol']}: {pos['qty']} shares @ ${float(pos.get('current_price', 0)):.2f} (P&L: ${pnl:.2f}, {pnl_pct:+.1f}%)"
            else:
                guidance += "\\n  No positions currently held"
            
            return guidance
            
        except Exception as e:
            return f"❌ Error getting trading guidance: {str(e)}"

    # =============================================================================
    # COMPATIBILITY METHODS (for backward compatibility)
    # =============================================================================
    
    def get_current_price(self, symbol: str) -> float:
        """Alias for get_real_price for backward compatibility"""
        return self.get_real_price(symbol)
    
    def _verify_connection(self):
        """Verify connection - delegated to base client"""
        # Connection is already verified in the specialized clients
        pass


if __name__ == "__main__":
    # Test the enhanced client
    print("Testing Enhanced Alpaca Client with Decomposed Architecture...")
    
    try:
        client = AlpacaClient(trader_name="Warren")
        
        print("\\n" + "="*50)
        print("TRADING GUIDANCE:")
        print(client.get_trading_guidance())
        
        print("\\n" + "="*50)
        print("PORTFOLIO REPORT:")
        print(client.get_portfolio_report())
        
        print("\\n✅ Enhanced Alpaca Client test completed!")
        
    except Exception as e:
        print(f"❌ Error testing Enhanced Alpaca Client: {e}")
        import traceback
        traceback.print_exc()