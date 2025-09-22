"""
Trading Client - Risk-managed trading operations.
Handles order execution with integrated risk management.
"""

import sys
import os
from typing import Dict, Any
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.base_alpaca_client import BaseAlpacaClient
from core.risk_manager import RiskManager
from utils.database import write_log


class TradingClient(BaseAlpacaClient):
    """
    Simple trading client that handles risk-managed trading operations.
    """
    
    def __init__(self, paper_trading: bool = True, trader_name: str = None, risk_manager: RiskManager = None, shared_connection=None):
        super().__init__(paper_trading, trader_name, shared_connection)
        
        # Initialize risk manager if not provided
        if risk_manager:
            self.risk_manager = risk_manager
        else:
            # Get strategy-specific risk limits
            strategy_risk_limits = self._get_strategy_risk_limits()
            self.risk_manager = RiskManager(self.trader_name, strategy_risk_limits)
    
    def _get_strategy_risk_limits(self) -> dict:
        """Get risk limits from the strategy for this trader"""
        try:
            # Import strategy system
            from strategies import create_strategy
            strategy_obj = create_strategy(self.trader_name)
            return strategy_obj.get_risk_limits()
        except Exception as e:
            print(f"⚠️ Could not load strategy risk limits: {e}")
            return {}
    
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
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for risk assessment - delegates to market data"""
        # Import here to avoid circular imports
        from core.market_data_client import MarketDataClient
        market_client = MarketDataClient(self.paper_trading, self.trader_name)
        return market_client.get_real_price(symbol)
    
    def get_portfolio_value(self) -> float:
        """Get portfolio value for risk assessment - delegates to account"""
        # Import here to avoid circular imports
        from core.account_client import AccountClient
        account_client = AccountClient(self.paper_trading, self.trader_name)
        return account_client.calculate_portfolio_value()
    
    def get_filled_orders_today(self) -> int:
        """Get count of filled orders today for risk assessment"""
        try:
            # Import here to avoid circular imports
            from core.account_client import AccountClient
            account_client = AccountClient(self.paper_trading, self.trader_name)
            
            today = datetime.now().strftime("%Y-%m-%d")
            orders = account_client.get_orders(status="filled", limit=100)
            today_trades = sum(1 for order in orders if order.get('filled_at') and str(order['filled_at']).startswith(today))
            return today_trades
        except:
            return 0
    
    def assess_trade_risk(self, symbol: str, quantity: int, conviction_level: int = 5) -> Dict[str, Any]:
        """
        Pre-trade risk assessment with scoring and recommendations.
        
        Args:
            symbol: Stock ticker symbol
            quantity: Number of shares (positive for buy, negative for sell)
            conviction_level: Trader's conviction level (1-10, 10 being highest)
            
        Returns:
            Dictionary with risk assessment results
        """
        try:
            # Get current price
            price = self.get_current_price(symbol)
            
            # Get portfolio value
            portfolio_value = self.get_portfolio_value()
            
            # Get filled orders today
            filled_orders_today = self.get_filled_orders_today()
            
            # Perform risk assessment
            assessment = self.risk_manager.assess_trade_risk(
                symbol=symbol,
                quantity=quantity,
                price=price,
                portfolio_value=portfolio_value,
                conviction_level=conviction_level,
                filled_orders_today=filled_orders_today
            )
            
            # Add trader name
            assessment["trader"] = self.trader_name
            
            return assessment
        except Exception as e:
            return {"error": f"Risk assessment error: {str(e)}"}
    
    def buy_shares_with_risk_management(self, symbol: str, quantity: int, rationale: str) -> str:
        """Execute buy order with integrated risk management and logging"""
        try:
            # Input validation
            if quantity <= 0:
                return "❌ Invalid quantity: must be positive"
            
            # Get current price
            price = self.get_current_price(symbol)
            
            # Risk management validation
            portfolio_value = self.get_portfolio_value()
            today_trades = self.get_filled_orders_today()
            
            is_valid, risk_message = self.risk_manager.validate_trade(symbol, quantity, price, portfolio_value, today_trades)
            if not is_valid:
                write_log(self.trader_name, "risk", f"Buy order rejected: {risk_message}")
                return f"❌ {risk_message}"
            
            # Check buying power
            from core.account_client import AccountClient
            account_client = AccountClient(self.paper_trading, self.trader_name)
            account_info = account_client.get_account_info()
            cash_balance = float(account_info.get("cash", 0))
            estimated_cost = price * quantity
            
            if estimated_cost > cash_balance:
                return f"❌ Insufficient funds: Need ${estimated_cost:,.2f}, have ${cash_balance:,.2f}"
            
            # Execute order
            order_result = self.place_market_order(symbol, quantity, "buy")
            
            if order_result.get("success", False):
                write_log(self.trader_name, "trading", f"✅ Buy {quantity} {symbol} at ${price:.2f} - {rationale}")
                
                # Get updated portfolio report
                portfolio_report = account_client.get_portfolio_report()
                return f"✅ Successfully bought {quantity} shares of {symbol} at ${price:.2f}\\n\\n{portfolio_report}"
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
            from core.account_client import AccountClient
            account_client = AccountClient(self.paper_trading, self.trader_name)
            positions = account_client.get_positions()
            current_position = next((pos for pos in positions if pos["symbol"] == symbol), None)
            
            if not current_position or float(current_position["qty"]) < quantity:
                available = float(current_position["qty"]) if current_position else 0
                return f"❌ Insufficient shares: Need {quantity}, have {available} shares of {symbol}"
            
            # Get current price
            price = self.get_current_price(symbol)
            
            # Risk management validation (mainly for daily limits)
            portfolio_value = self.get_portfolio_value()
            today_trades = self.get_filled_orders_today()
            
            is_valid, risk_message = self.risk_manager.validate_trade(symbol, quantity, price, portfolio_value, today_trades)
            if not is_valid:
                write_log(self.trader_name, "risk", f"Sell order rejected: {risk_message}")
                return f"❌ {risk_message}"
            
            # Execute order
            order_result = self.place_market_order(symbol, quantity, "sell")
            
            if order_result.get("success", False):
                write_log(self.trader_name, "trading", f"✅ Sell {quantity} {symbol} at ${price:.2f} - {rationale}")
                
                # Get updated portfolio report
                portfolio_report = account_client.get_portfolio_report()
                return f"✅ Successfully sold {quantity} shares of {symbol} at ${price:.2f}\\n\\n{portfolio_report}"
            else:
                error_msg = order_result.get("error", "Unknown error")
                write_log(self.trader_name, "error", f"❌ Sell order failed: {error_msg}")
                return f"❌ Sell order failed: {error_msg}"
                
        except Exception as e:
            write_log(self.trader_name, "error", f"❌ Sell order exception: {str(e)}")
            return f"❌ Error executing sell order: {str(e)}"
