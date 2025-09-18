"""
Production Account System - Enhanced account management with real Alpaca trading integration.
Extends the base Account class with live trading capabilities and broker synchronization.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.alpaca_client import AlpacaClient
from utils.database import write_account, read_account, write_log
from datetime import datetime
from typing import Dict, Any, Optional
import json
import os
from dotenv import load_dotenv

load_dotenv()

class Transaction:
    """Simple transaction record for trading operations"""
    def __init__(self, symbol: str, quantity: int, price: float, timestamp: str, rationale: str):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp
        self.rationale = rationale

class ProductionAccount:
    """
    Production-ready account class with real Alpaca trading integration.
    Simplified to avoid Pydantic inheritance issues while maintaining functionality.
    """
    
    def __init__(self, name: str, paper_trading: bool = True):
        # Core account attributes
        self.name = name.lower()
        self.balance = 0.0
        self.strategy = ""
        self.holdings = {}
        self.transactions = []
        self.portfolio_value_time_series = []
        
        # Production-specific attributes
        self.paper_trading = paper_trading
        self.alpaca = AlpacaClient(paper_trading, trader_name=name)
        self.last_sync_time = None
        self.risk_limits = self._load_risk_limits()
        
        # Load or create account data
        self._load_or_create_account()
    
    def _load_risk_limits(self) -> Dict[str, float]:
        """Load risk management limits from environment"""
        return {
            "max_position_size": float(os.getenv("MAX_POSITION_SIZE", "1000")),
            "max_daily_trades": int(os.getenv("MAX_DAILY_TRADES", "10")),
            "max_portfolio_risk": float(os.getenv("MAX_PORTFOLIO_RISK", "0.02"))  # 2% max risk
        }
    
    def _load_or_create_account(self):
        """Load existing account or create new one with Alpaca sync"""
        try:
            fields = read_account(self.name)
            if fields:
                # Load existing account data
                self.balance = fields.get("balance", 0.0)
                self.strategy = fields.get("strategy", "")
                self.holdings = fields.get("holdings", {})
                self.transactions = [Transaction(**t) for t in fields.get("transactions", [])]
                self.portfolio_value_time_series = fields.get("portfolio_value_time_series", [])
                self.last_sync_time = fields.get("last_sync_time")
                
                write_log(self.name, "account", f"Loaded existing account data")
            else:
                # New account - sync with Alpaca
                write_log(self.name, "account", f"Creating new production account")
                self.sync_with_alpaca()
        
        except Exception as e:
            write_log(self.name, "account", f"Error loading account: {str(e)}")
            # Fall back to default initialization
            self.balance = 10000.0  # Default paper trading balance
            self.strategy = "Conservative Growth"
            self.save()
    
    def sync_with_alpaca(self) -> str:
        """
        Synchronize local account state with Alpaca broker account.
        Updates balance, holdings, and recent transactions.
        """
        try:
            write_log(self.name, "account", "Starting Alpaca sync...")
            
            # Get account information
            account_info = self.alpaca.get_account_info()
            if "error" in account_info:
                return f"Sync failed - Account info error: {account_info['error']}"
            
            # Update balance from broker
            self.balance = account_info["cash"]
            
            # Get current positions
            positions = self.alpaca.get_positions()
            
            # Update holdings from broker positions
            self.holdings = {}
            for pos in positions:
                if pos["qty"] != 0:
                    self.holdings[pos["symbol"]] = pos["qty"]
            
            # Update timestamp
            self.last_sync_time = datetime.now().isoformat()
            
            # Save updated state
            self.save()
            
            sync_message = f"✅ Successfully synced with Alpaca - Cash: ${self.balance:,.2f}, Positions: {len(self.holdings)}"
            write_log(self.name, "account", sync_message)
            
            return sync_message
            
        except Exception as e:
            error_message = f"Sync failed: {str(e)}"
            write_log(self.name, "account", error_message)
            return error_message
    
    def get_real_price(self, symbol: str) -> float:
        """Get real-time price from Alpaca instead of simulation"""
        return self.alpaca.get_real_price(symbol)
    
    def _validate_trade_risk(self, symbol: str, quantity: int, action: str, price: float) -> tuple[bool, str]:
        """
        Validate trade against risk management rules.
        
        Returns:
            (is_valid, message) tuple
        """
        try:
            trade_value = abs(quantity) * price
            portfolio_value = self.calculate_portfolio_value()
            
            # Check position size limit
            if trade_value > self.risk_limits["max_position_size"]:
                return False, f"Trade value ${trade_value:,.2f} exceeds max position size ${self.risk_limits['max_position_size']:,.2f}"
            
            # Check portfolio risk (simple implementation)
            if portfolio_value > 0:
                risk_percentage = trade_value / portfolio_value
                if risk_percentage > self.risk_limits["max_portfolio_risk"]:
                    return False, f"Trade represents {risk_percentage*100:.1f}% of portfolio, exceeds {self.risk_limits['max_portfolio_risk']*100:.1f}% limit"
            
            # Check daily trade limit (count today's transactions)
            today = datetime.now().strftime("%Y-%m-%d")
            today_trades = sum(1 for t in self.transactions if t.timestamp.startswith(today))
            if today_trades >= self.risk_limits["max_daily_trades"]:
                return False, f"Daily trade limit of {self.risk_limits['max_daily_trades']} reached"
            
            return True, "Trade approved"
            
        except Exception as e:
            return False, f"Risk validation error: {str(e)}"
    
    def buy_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        """
        Execute buy order with real Alpaca integration and risk management.
        """
        try:
            # Input validation
            if quantity <= 0:
                return "❌ Invalid quantity: must be positive"
            
            # Get current price
            current_price = self.get_real_price(symbol)
            if current_price <= 0:
                return f"❌ Could not get price for {symbol}"
            
            # Risk management validation
            is_valid, risk_message = self._validate_trade_risk(symbol, quantity, "buy", current_price)
            if not is_valid:
                write_log(self.name, "risk", f"Buy order rejected: {risk_message}")
                return f"❌ {risk_message}"
            
            estimated_cost = current_price * quantity
            
            # Check buying power
            if estimated_cost > self.balance:
                return f"❌ Insufficient funds: Need ${estimated_cost:,.2f}, have ${self.balance:,.2f}"
            
            # Execute real order if enabled
            execute_real_orders = os.getenv("EXECUTE_REAL_ORDERS", "false").lower() == "true"
            if execute_real_orders:
                order_result = self.alpaca.place_market_order(symbol, quantity, "buy")
                
                if not order_result.get("success", False):
                    error_msg = f"❌ Real order failed: {order_result.get('error', 'Unknown error')}"
                    write_log(self.name, "trading", error_msg)
                    return error_msg
                
                write_log(self.name, "trading", f"🔥 REAL ORDER EXECUTED: Buy {quantity} {symbol} at ~${current_price:.2f}")
                
                # Use actual fill price if available
                actual_price = order_result.get("avg_fill_price", current_price)
            else:
                actual_price = current_price
                write_log(self.name, "trading", f"📝 SIMULATED: Buy {quantity} {symbol} at ${current_price:.2f}")
            
            # Update local state
            total_cost = actual_price * quantity
            self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
            self.balance -= total_cost
            
            # Record transaction
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            transaction = Transaction(
                symbol=symbol,
                quantity=quantity,
                price=actual_price,
                timestamp=timestamp,
                rationale=rationale
            )
            self.transactions.append(transaction)
            
            # Save state
            self.save()
            
            success_msg = f"✅ Successfully bought {quantity} shares of {symbol} at ${actual_price:.2f}"
            write_log(self.name, "account", success_msg)
            
            return f"{success_msg}\n\n{self.report()}"
            
        except Exception as e:
            error_msg = f"❌ Buy order failed: {str(e)}"
            write_log(self.name, "account", error_msg)
            return error_msg
    
    def sell_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        """
        Execute sell order with real Alpaca integration and risk management.
        """
        try:
            # Input validation
            if quantity <= 0:
                return "❌ Invalid quantity: must be positive"
            
            current_holdings = self.holdings.get(symbol, 0)
            if current_holdings < quantity:
                return f"❌ Cannot sell {quantity} shares of {symbol}. Only have {current_holdings} shares."
            
            # Get current price
            current_price = self.get_real_price(symbol)
            if current_price <= 0:
                return f"❌ Could not get price for {symbol}"
            
            # Risk management validation (for position sizing)
            is_valid, risk_message = self._validate_trade_risk(symbol, -quantity, "sell", current_price)
            if not is_valid:
                write_log(self.name, "risk", f"Sell order rejected: {risk_message}")
                return f"❌ {risk_message}"
            
            # Execute real order if enabled
            execute_real_orders = os.getenv("EXECUTE_REAL_ORDERS", "false").lower() == "true"
            if execute_real_orders:
                order_result = self.alpaca.place_market_order(symbol, quantity, "sell")
                
                if not order_result.get("success", False):
                    error_msg = f"❌ Real order failed: {order_result.get('error', 'Unknown error')}"
                    write_log(self.name, "trading", error_msg)
                    return error_msg
                
                write_log(self.name, "trading", f"🔥 REAL ORDER EXECUTED: Sell {quantity} {symbol} at ~${current_price:.2f}")
                
                # Use actual fill price if available
                actual_price = order_result.get("avg_fill_price", current_price)
            else:
                actual_price = current_price
                write_log(self.name, "trading", f"📝 SIMULATED: Sell {quantity} {symbol} at ${current_price:.2f}")
            
            # Update local state
            total_proceeds = actual_price * quantity
            self.holdings[symbol] -= quantity
            
            # Remove holding if completely sold
            if self.holdings[symbol] == 0:
                del self.holdings[symbol]
            
            self.balance += total_proceeds
            
            # Record transaction (negative quantity for sells)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            transaction = Transaction(
                symbol=symbol,
                quantity=-quantity,  # Negative for sell
                price=actual_price,
                timestamp=timestamp,
                rationale=rationale
            )
            self.transactions.append(transaction)
            
            # Save state
            self.save()
            
            success_msg = f"✅ Successfully sold {quantity} shares of {symbol} at ${actual_price:.2f}"
            write_log(self.name, "account", success_msg)
            
            return f"{success_msg}\n\n{self.report()}"
            
        except Exception as e:
            error_msg = f"❌ Sell order failed: {str(e)}"
            write_log(self.name, "account", error_msg)
            return error_msg
    
    def calculate_portfolio_value(self) -> float:
        """Calculate total portfolio value using real Alpaca prices"""
        total_value = self.balance
        
        for symbol, quantity in self.holdings.items():
            current_price = self.get_real_price(symbol)
            if current_price > 0:
                total_value += current_price * quantity
            else:
                write_log(self.name, "account", f"Warning: Could not get price for {symbol}")
        
        return total_value
    
    def get_detailed_report(self) -> str:
        """Enhanced report with production-specific information"""
        base_report = self.report()
        
        # Add production-specific details
        portfolio_value = self.calculate_portfolio_value()
        
        production_details = f"""
🏭 PRODUCTION ACCOUNT DETAILS:
• Trading Mode: {'📄 Paper Trading' if self.paper_trading else '💰 Live Trading'}
• Real Orders: {'✅ Enabled' if os.getenv('EXECUTE_REAL_ORDERS', 'false') == 'true' else '❌ Disabled'}
• Last Sync: {self.last_sync_time or 'Never'}
• Risk Limits: Max Position ${self.risk_limits['max_position_size']:,.0f}, Max Daily Trades {self.risk_limits['max_daily_trades']}

📊 REAL-TIME PORTFOLIO:
• Cash Balance: ${self.balance:,.2f}
• Holdings Value: ${portfolio_value - self.balance:,.2f}
• Total Portfolio: ${portfolio_value:,.2f}
"""
        
        return base_report + production_details
    
    def save(self):
        """Enhanced save with production-specific fields"""
        data = {
            "name": self.name,
            "balance": self.balance,
            "strategy": self.strategy,
            "holdings": self.holdings,
            "transactions": [
                {
                    "symbol": t.symbol,
                    "quantity": t.quantity,
                    "price": t.price,
                    "timestamp": t.timestamp,
                    "rationale": t.rationale
                } for t in self.transactions
            ],
            "portfolio_value_time_series": self.portfolio_value_time_series,
            "last_sync_time": self.last_sync_time,
            "paper_trading": self.paper_trading,
            "risk_limits": self.risk_limits
        }
        write_account(self.name, data)
    
    def report(self) -> str:
        """Generate account report similar to base Account class"""
        portfolio_value = self.calculate_portfolio_value()
        profit_loss = portfolio_value - 10000.0  # Assuming 10k initial
        
        report = f"""
📊 ACCOUNT REPORT - {self.name.upper()}
💰 Cash Balance: ${self.balance:,.2f}
📈 Portfolio Value: ${portfolio_value:,.2f}
📊 Total P&L: ${profit_loss:,.2f} ({(profit_loss/10000)*100:.1f}%)

🏢 Holdings ({len(self.holdings)} positions):"""
        
        for symbol, quantity in self.holdings.items():
            current_price = self.get_real_price(symbol)
            value = current_price * quantity
            report += f"\n  • {symbol}: {quantity} shares @ ${current_price:.2f} = ${value:,.2f}"
        
        if not self.holdings:
            report += "\n  (No current positions)"
        
        report += f"\n\n📋 Recent Transactions: {len(self.transactions)}"
        
        return report
    
    def get_strategy(self) -> str:
        """Get current strategy"""
        return self.strategy or "No strategy set"
    
    def change_strategy(self, strategy: str) -> str:
        """Change investment strategy"""
        old_strategy = self.strategy
        self.strategy = strategy
        self.save()
        return f"Strategy updated from '{old_strategy}' to '{strategy}'"
    
    @classmethod
    def get(cls, name: str, paper_trading: bool = True):
        """Get or create a production account"""
        return cls(name, paper_trading)

if __name__ == "__main__":
    # Test the production account
    print("Testing Production Account...")
    
    account = ProductionAccount("test_trader", paper_trading=True)
    print(account.get_detailed_report())
    
    # Test sync
    sync_result = account.sync_with_alpaca()
    print(f"Sync Result: {sync_result}")
