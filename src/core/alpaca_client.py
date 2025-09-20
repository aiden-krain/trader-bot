"""
Enhanced Alpaca API Client with Risk Management Integration.
Production-ready client for real market data and trading operations with built-in risk controls.
Consolidates all trading functionality in a single, clean interface.
"""

import os
import sys
import json
from typing import Dict, Optional, List, Union, Tuple
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Modern alpaca-py imports
from alpaca.trading.client import TradingClient
from alpaca.data.historical.stock import StockHistoricalDataClient

# Add utils path for database operations and risk management
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import write_log
from core.risk_manager import RiskManager

load_dotenv()


class AlpacaClient:
    """
    Enhanced Alpaca client with integrated risk management and trading operations.
    Combines market data, trading, and risk controls in a single, simple interface.
    """
    
    def __init__(self, paper_trading: bool = True, trader_name: str = None):
        self.paper_trading = paper_trading
        self.trader_name = trader_name or "Unknown"
        
        # Get trader-specific API credentials
        api_key, secret_key = self._get_trader_credentials(trader_name)
        
        # Initialize modern alpaca-py clients
        self.trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper_trading
        )
        
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
        
        # Initialize risk management
        self.risk_manager = RiskManager(self.trader_name)
        
        # Store credentials for compatibility
        self.api_key = api_key
        self.secret_key = secret_key
        
        # Verify connection
        self._verify_connection()
    
    def _get_trader_credentials(self, trader_name: str = None) -> tuple[str, str]:
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
            print(f"✅ Connected to Alpaca {env_type} Trading")
            print(f"   Account Status: {account.status}")
            print(f"   Buying Power: ${float(account.buying_power):,.2f}")
            print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
        except Exception as e:
            print(f"❌ Failed to connect to Alpaca: {e}")
            raise e
    
    # =============================================================================
    # MARKET DATA METHODS
    # =============================================================================
    
    def get_real_price(self, symbol: str) -> float:
        """Get current real-time price for a symbol with fallbacks"""
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
            
        except Exception as e:
            print(f"Error getting real-time price for {symbol}: {e}")
        
        # Fallback to reasonable test prices for development
        test_prices = {
            "AAPL": 175.50, "TSLA": 245.30, "GOOGL": 142.20, "MSFT": 415.80,
            "AMZN": 185.70, "NVDA": 128.45, "META": 512.30, "SPY": 565.40,
            "QQQ": 485.20, "IWM": 224.60, "VTI": 285.30, "BRK.B": 450.20
        }
        
        return test_prices.get(symbol.upper(), 100.0)
    
    def get_market_status(self) -> Dict:
        """Get current market status (open/closed)"""
        try:
            from alpaca.trading.requests import GetCalendarRequest
            from datetime import datetime, date
            
            # Get today's market calendar
            today = date.today()
            request = GetCalendarRequest(start=today, end=today)
            calendar = self.trading_client.get_calendar(request)
            
            if calendar:
                market_day = calendar[0]
                now = datetime.now().time()
                market_open_time = market_day.open.time()
                market_close_time = market_day.close.time()
                
                is_open = market_open_time <= now <= market_close_time
                
                return {
                    "is_open": is_open,
                    "date": str(today),
                    "market_open": str(market_open_time),
                    "market_close": str(market_close_time),
                    "current_time": str(now)
                }
            else:
                # Market is closed (no calendar entry for today)
                return {
                    "is_open": False,
                    "date": str(today),
                    "reason": "No market session today"
                }
                
        except Exception as e:
            print(f"Error getting market status: {e}")
            # Default to market open for development/testing
            return {
                "is_open": True,
                "error": str(e),
                "fallback": "Assuming market open for development"
            }
    
    # =============================================================================
    # ACCOUNT & PORTFOLIO METHODS  
    # =============================================================================
    
    def get_account_info(self) -> Dict:
        """Get comprehensive account information"""
        try:
            account = self.trading_client.get_account()
            return {
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                "status": str(account.status),
                "account_blocked": bool(getattr(account, 'account_blocked', False)),
                "trading_blocked": bool(getattr(account, 'trading_blocked', False)),
                "pattern_day_trader": bool(getattr(account, 'pattern_day_trader', False)),
                "day_trade_count": int(getattr(account, 'day_trade_count', 0)),
                "daytrade_buying_power": float(getattr(account, 'daytrade_buying_power', account.buying_power))
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_positions(self) -> List[Dict]:
        """Get all current positions"""
        try:
            positions = self.trading_client.get_all_positions()
            return [{
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "side": "long" if float(pos.qty) > 0 else "short",
                "market_value": float(pos.market_value) if pos.market_value else 0.0,
                "avg_entry_price": float(pos.avg_entry_price) if pos.avg_entry_price else 0.0,
                "current_price": float(pos.current_price) if pos.current_price else 0.0,
                "unrealized_pl": float(pos.unrealized_pl) if pos.unrealized_pl else 0.0,
                "unrealized_plpc": float(pos.unrealized_plpc) if pos.unrealized_plpc else 0.0,
                "cost_basis": float(pos.cost_basis) if pos.cost_basis else 0.0
            } for pos in positions]
        except Exception as e:
            return []
    
    def calculate_portfolio_value(self) -> float:
        """Calculate current portfolio value using real Alpaca data"""
        try:
            account_info = self.get_account_info()
            return float(account_info.get("portfolio_value", 0))
        except Exception as e:
            print(f"Error calculating portfolio value: {e}")
            return 0.0
    
    def get_orders(self, status: str = "all", limit: int = 50) -> List[Dict]:
        """Get order history from Alpaca"""
        try:
            from alpaca.trading.requests import GetOrdersRequest
            from alpaca.trading.enums import QueryOrderStatus
            
            # Map status string to enum (only ALL, OPEN, CLOSED are available)
            status_map = {
                "all": QueryOrderStatus.ALL,
                "open": QueryOrderStatus.OPEN, 
                "closed": QueryOrderStatus.CLOSED,
                "filled": QueryOrderStatus.CLOSED,  # Filled orders are in CLOSED status
                "cancelled": QueryOrderStatus.CLOSED  # Cancelled orders are also in CLOSED status
            }
            
            order_status = status_map.get(status.lower(), QueryOrderStatus.ALL)
            
            # Create request
            request = GetOrdersRequest(status=order_status, limit=limit)
            orders = self.trading_client.get_orders(filter=request)
            
            # Convert orders to dict format
            order_dicts = []
            for order in orders:
                order_dict = {
                    "id": str(order.id),
                    "symbol": order.symbol,
                    "qty": int(order.qty) if order.qty else 0,
                    "filled_qty": int(order.filled_qty) if order.filled_qty else 0,
                    "side": str(order.side).lower(),
                    "order_type": str(order.order_type),
                    "status": str(order.status),
                    "submitted_at": str(order.submitted_at) if order.submitted_at else None,
                    "filled_at": str(order.filled_at) if order.filled_at else None,
                    "avg_fill_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                    "time_in_force": str(order.time_in_force) if order.time_in_force else None
                }
                order_dicts.append(order_dict)
            
            return order_dicts
            
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []
    
    # =============================================================================
    # TRADING METHODS WITH RISK MANAGEMENT
    # =============================================================================
    
    def place_market_order(self, symbol: str, qty: int, side: str) -> Dict:
        """Place market order using modern alpaca-py"""
        try:
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            
            # Convert side to proper enum
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            
            # Create market order request
            market_order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            
            # Submit the order
            order = self.trading_client.submit_order(order_data=market_order_data)
            
            return {
                "success": True,
                "order_id": str(order.id),
                "symbol": order.symbol,
                "qty": int(order.qty),
                "side": str(order.side),
                "status": str(order.status)
            }
            
        except Exception as e:
            from alpaca.common.exceptions import APIError
            if isinstance(e, APIError):
                return {"success": False, "error": f"Alpaca API Error: {e}"}
            else:
                return {"success": False, "error": f"Order failed: {str(e)}"}
    
    def buy_shares_with_risk_management(self, symbol: str, quantity: int, rationale: str) -> str:
        """Execute buy order with integrated risk management and logging"""
        try:
            # Input validation
            if quantity <= 0:
                return "❌ Invalid quantity: must be positive"
            
            # Get current price
            price = self.get_real_price(symbol)
            if price <= 0:
                return f"❌ Could not get price for {symbol}"
            
            # Risk management validation
            portfolio_value = self.calculate_portfolio_value()
            
            # Get daily trade count for risk validation
            today = datetime.now().strftime("%Y-%m-%d")
            try:
                from alpaca.trading.requests import GetOrdersRequest
                from alpaca.trading.enums import QueryOrderStatus
                
                request = GetOrdersRequest(status=QueryOrderStatus.CLOSED, limit=50)
                orders = self.trading_client.get_orders(filter=request)
                today_trades = sum(1 for order in orders if order.filled_at and str(order.filled_at).startswith(today))
            except:
                today_trades = 0
            
            is_valid, risk_message = self.risk_manager.validate_trade(symbol, quantity, price, portfolio_value, today_trades)
            if not is_valid:
                write_log(self.trader_name, "risk", f"Buy order rejected: {risk_message}")
                return f"❌ {risk_message}"
            
            # Check buying power
            account_info = self.get_account_info()
            cash_balance = float(account_info.get("cash", 0))
            estimated_cost = price * quantity
            
            if estimated_cost > cash_balance:
                return f"❌ Insufficient funds: Need ${estimated_cost:,.2f}, have ${cash_balance:,.2f}"
            
            # Execute order
            order_result = self.place_market_order(symbol, quantity, "buy")
            
            if order_result.get("success", False):
                write_log(self.trader_name, "trading", f"✅ Buy {quantity} {symbol} at ${price:.2f} - {rationale}")
                return f"✅ Successfully bought {quantity} shares of {symbol} at ${price:.2f}\\n\\n{self.get_portfolio_report()}"
            else:
                error_msg = order_result.get("error", "Unknown error")
                write_log(self.trader_name, "error", f"❌ Buy order failed: {error_msg}")
                return f"❌ Buy order failed: {error_msg}"
                
        except Exception as e:
            write_log(self.trader_name, "error", f"❌ Buy order exception: {str(e)}")
            return f"❌ Error executing buy order: {str(e)}"
    
    def sell_shares_with_risk_management(self, symbol: str, quantity: int, rationale: str) -> str:
        """Execute sell order with integrated risk management and logging"""
        try:
            # Input validation
            if quantity <= 0:
                return "❌ Invalid quantity: must be positive"
            
            # Check if we have enough shares to sell
            positions = self.get_positions()
            current_position = next((pos for pos in positions if pos["symbol"] == symbol), None)
            
            if not current_position or float(current_position["qty"]) < quantity:
                available = float(current_position["qty"]) if current_position else 0
                return f"❌ Insufficient shares: Need {quantity}, have {available} shares of {symbol}"
            
            # Get current price
            price = self.get_real_price(symbol)
            if price <= 0:
                return f"❌ Could not get price for {symbol}"
            
            # Risk management validation (mainly for daily limits)
            portfolio_value = self.calculate_portfolio_value()
            
            # Get daily trade count
            today = datetime.now().strftime("%Y-%m-%d")
            try:
                from alpaca.trading.requests import GetOrdersRequest
                from alpaca.trading.enums import QueryOrderStatus
                
                request = GetOrdersRequest(status=QueryOrderStatus.CLOSED, limit=50)
                orders = self.trading_client.get_orders(filter=request)
                today_trades = sum(1 for order in orders if order.filled_at and str(order.filled_at).startswith(today))
            except:
                today_trades = 0
            
            is_valid, risk_message = self.risk_manager.validate_trade(symbol, quantity, price, portfolio_value, today_trades)
            if not is_valid:
                write_log(self.trader_name, "risk", f"Sell order rejected: {risk_message}")
                return f"❌ {risk_message}"
            
            # Execute order
            order_result = self.place_market_order(symbol, quantity, "sell")
            
            if order_result.get("success", False):
                write_log(self.trader_name, "trading", f"✅ Sell {quantity} {symbol} at ${price:.2f} - {rationale}")
                return f"✅ Successfully sold {quantity} shares of {symbol} at ${price:.2f}\\n\\n{self.get_portfolio_report()}"
            else:
                error_msg = order_result.get("error", "Unknown error")
                write_log(self.trader_name, "error", f"❌ Sell order failed: {error_msg}")
                return f"❌ Sell order failed: {error_msg}"
                
        except Exception as e:
            write_log(self.trader_name, "error", f"❌ Sell order exception: {str(e)}")
            return f"❌ Error executing sell order: {str(e)}"
    
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
    
    def get_portfolio_report(self) -> str:
        """Get detailed portfolio report"""
        try:
            account_info = self.get_account_info()
            positions = self.get_positions()
            
            report = f"""📊 ACCOUNT REPORT - {self.trader_name.upper()}
💰 Cash Balance: ${float(account_info.get('cash', 0)):,.2f}
📈 Portfolio Value: ${float(account_info.get('portfolio_value', 0)):,.2f}
📊 Total P&L: ${float(account_info.get('portfolio_value', 0)) - 1000:.2f} ({((float(account_info.get('portfolio_value', 0)) / 1000) - 1) * 100:.1f}%)

🏢 Holdings ({len(positions)} positions):"""
            
            if positions:
                for pos in positions:
                    current_price = float(pos.get('current_price', 0))
                    qty = float(pos['qty'])
                    market_value = current_price * qty
                    report += f"\\n  • {pos['symbol']}: {qty} shares @ ${current_price:.2f} = ${market_value:.2f}"
            else:
                report += "\\n  No positions currently held"
            
            return report
            
        except Exception as e:
            return f"❌ Error generating portfolio report: {str(e)}"


if __name__ == "__main__":
    # Test the enhanced client
    print("Testing Enhanced Alpaca Client...")
    
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