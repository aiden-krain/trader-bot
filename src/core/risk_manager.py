"""
Simple Risk Management System for Trading Operations.
Handles trade validation, position limits, and risk controls.
"""

import os
from typing import Dict, Tuple, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class RiskManager:
    """Simple, focused risk management for trading operations"""
    
    def __init__(self, trader_name: str = "Unknown"):
        self.trader_name = trader_name
        self.risk_limits = self._load_risk_limits()
    
    def _load_risk_limits(self) -> Dict[str, float]:
        """Load risk management limits from environment variables"""
        return {
            "max_position_size": float(os.getenv("MAX_POSITION_SIZE", "1000")),
            "max_portfolio_risk": float(os.getenv("MAX_PORTFOLIO_RISK", "0.5")),  # 50%
            "max_daily_trades": int(os.getenv("MAX_DAILY_TRADES", "10"))
        }
    
    def validate_trade(self, symbol: str, quantity: int, price: float, 
                      portfolio_value: float, filled_orders_today: int = 0) -> Tuple[bool, str]:
        """
        Validate a trade against all risk management rules.
        
        Args:
            symbol: Stock ticker symbol
            quantity: Number of shares (positive for buy, negative for sell)
            price: Current stock price
            portfolio_value: Current portfolio value
            filled_orders_today: Number of filled orders today (optional)
        
        Returns:
            (is_valid, message) tuple
        """
        try:
            trade_value = abs(quantity) * price
            
            # Check position size limit
            if trade_value > self.risk_limits["max_position_size"]:
                return False, f"Trade value ${trade_value:,.2f} exceeds max position size ${self.risk_limits['max_position_size']:,.2f}"
            
            # Check portfolio risk percentage
            if portfolio_value > 0:
                risk_percentage = trade_value / portfolio_value
                if risk_percentage > self.risk_limits["max_portfolio_risk"]:
                    return False, f"Trade represents {risk_percentage*100:.1f}% of portfolio, exceeds {self.risk_limits['max_portfolio_risk']*100:.1f}% limit"
            
            # Check daily trade limit
            if filled_orders_today >= self.risk_limits["max_daily_trades"]:
                return False, f"Daily trade limit of {self.risk_limits['max_daily_trades']} reached (current: {filled_orders_today})"
            
            return True, "Trade approved"
            
        except Exception as e:
            return False, f"Risk validation error: {str(e)}"
    
    def check_position_size(self, trade_value: float) -> Tuple[bool, str]:
        """Check if trade value exceeds position size limits"""
        if trade_value > self.risk_limits["max_position_size"]:
            return False, f"Trade value ${trade_value:,.2f} exceeds max position size ${self.risk_limits['max_position_size']:,.2f}"
        return True, "Position size OK"
    
    def check_portfolio_risk(self, trade_value: float, portfolio_value: float) -> Tuple[bool, str]:
        """Check if trade exceeds portfolio risk percentage"""
        if portfolio_value <= 0:
            return True, "Portfolio risk check skipped (zero portfolio value)"
        
        risk_percentage = trade_value / portfolio_value
        if risk_percentage > self.risk_limits["max_portfolio_risk"]:
            return False, f"Trade represents {risk_percentage*100:.1f}% of portfolio, exceeds {self.risk_limits['max_portfolio_risk']*100:.1f}% limit"
        
        return True, f"Portfolio risk OK ({risk_percentage*100:.1f}%)"
    
    def check_daily_trade_limit(self, filled_orders_today: int) -> Tuple[bool, str]:
        """Check if daily trade limit is reached"""
        if filled_orders_today >= self.risk_limits["max_daily_trades"]:
            return False, f"Daily trade limit of {self.risk_limits['max_daily_trades']} reached (current: {filled_orders_today})"
        
        remaining = self.risk_limits["max_daily_trades"] - filled_orders_today
        return True, f"Daily trades OK ({remaining} remaining)"
    
    def get_risk_summary(self) -> Dict[str, str]:
        """Get a summary of current risk limits"""
        return {
            "trader": self.trader_name,
            "max_position_size": f"${self.risk_limits['max_position_size']:,.2f}",
            "max_portfolio_risk": f"{self.risk_limits['max_portfolio_risk']*100:.1f}%",
            "max_daily_trades": str(self.risk_limits['max_daily_trades'])
        }


if __name__ == "__main__":
    # Simple test
    risk_manager = RiskManager("TestTrader")
    
    print("Risk Manager Test:")
    print(f"Risk Limits: {risk_manager.get_risk_summary()}")
    
    # Test validation
    is_valid, msg = risk_manager.validate_trade("AAPL", 5, 150.0, 10000.0, 2)
    print(f"Trade validation: {is_valid} - {msg}")