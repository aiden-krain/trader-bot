"""
Clean Risk Management System for Trading Operations.
Uses strategy-provided risk limits as the primary source with sensible defaults.
"""

from typing import Dict, Tuple, Any


class RiskManager:
    """Clean, focused risk management using strategy-provided limits"""
    
    def __init__(self, trader_name: str = "Unknown", strategy_risk_limits: Dict = None):
        self.trader_name = trader_name
        self.risk_limits = self._load_risk_limits(strategy_risk_limits)
    
    def _load_risk_limits(self, strategy_risk_limits: Dict = None) -> Dict[str, Any]:
        """Load risk management limits from strategy with sensible defaults"""
        # Sensible default risk limits
        default_limits = {
            "max_position_size": 1000,      # $1000 default position size
            "max_portfolio_risk": 0.03,     # 3% portfolio risk
            "max_daily_trades": 5           # 5 trades per day default
        }
        
        # If strategy provides risk limits, use those as the primary source
        if strategy_risk_limits:
            # Start with defaults and update with strategy-specific limits
            limits = default_limits.copy()
            limits.update(strategy_risk_limits)
            return limits
        else:
            return default_limits
    
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
        summary = {
            "trader": self.trader_name,
            "max_position_size": f"${self.risk_limits['max_position_size']:,.2f}",
            "max_portfolio_risk": f"{self.risk_limits['max_portfolio_risk']*100:.1f}%",
            "max_daily_trades": str(self.risk_limits['max_daily_trades'])
        }
        
        # Add any additional risk limits from strategy
        for key, value in self.risk_limits.items():
            if key not in ['max_position_size', 'max_portfolio_risk', 'max_daily_trades']:
                # Format percentages nicely
                if isinstance(value, float) and (key.endswith('risk') or key.endswith('tolerance') or key.endswith('rate')):
                    summary[key] = f"{value*100:.1f}%"
                else:
                    summary[key] = str(value)
        
        return summary
    
    def assess_trade_risk(self, symbol: str, quantity: int, price: float, 
                         portfolio_value: float, conviction_level: int = 5,
                         filled_orders_today: int = 0) -> Dict[str, Any]:
        """
        Pre-trade risk assessment with scoring and recommendations.
        
        Args:
            symbol: Stock ticker symbol
            quantity: Number of shares (positive for buy, negative for sell)
            price: Current stock price
            portfolio_value: Current portfolio value
            conviction_level: Trader's conviction level (1-10, 10 being highest)
            filled_orders_today: Number of filled orders today
            
        Returns:
            Dictionary with risk assessment results
        """
        trade_value = abs(quantity) * price
        risk_percentage = trade_value / portfolio_value if portfolio_value > 0 else 0
        
        # Calculate risk score (0-100, lower is safer)
        position_size_score = min(100, (trade_value / self.risk_limits["max_position_size"]) * 100)
        portfolio_risk_score = min(100, (risk_percentage / self.risk_limits["max_portfolio_risk"]) * 100)
        daily_trades_score = min(100, (filled_orders_today / self.risk_limits["max_daily_trades"]) * 80)
        
        # Adjust for risk tolerance if strategy provides it
        risk_tolerance_factor = {
            "low": 1.2,      # Low tolerance = higher risk score
            "medium": 1.0,   # Medium tolerance = neutral
            "high": 0.8      # High tolerance = lower risk score
        }.get(self.risk_limits.get("risk_tolerance", "medium"), 1.0)
        
        # Calculate overall risk score
        overall_score = (position_size_score * 0.4 + 
                        portfolio_risk_score * 0.4 + 
                        daily_trades_score * 0.2) * risk_tolerance_factor
        
        # Generate warnings
        warnings = []
        if position_size_score > 80:
            warnings.append(f"Position size (${trade_value:,.2f}) is {position_size_score:.1f}% of your limit")
        if portfolio_risk_score > 80:
            warnings.append(f"Portfolio risk ({risk_percentage*100:.1f}%) is {portfolio_risk_score:.1f}% of your limit")
        if daily_trades_score > 80:
            warnings.append(f"Daily trade count ({filled_orders_today}) is {daily_trades_score:.1f}% of your limit")
        
        # Calculate recommended position size based on conviction
        conviction_factor = conviction_level / 10  # 0.1 to 1.0
        max_recommended_value = self.risk_limits["max_position_size"] * conviction_factor
        recommended_quantity = int(max_recommended_value / price) if price > 0 else 0
        
        # Prepare assessment result
        assessment = {
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "trade_value": trade_value,
            "portfolio_percentage": risk_percentage * 100,
            "risk_score": min(100, overall_score),  # 0-100 scale
            "risk_level": self._get_risk_level(overall_score),
            "warnings": warnings,
            "recommended_quantity": recommended_quantity,
            "recommended_value": recommended_quantity * price,
            "conviction_level": conviction_level,
            "is_valid": overall_score < 100  # Trade is valid if score < 100
        }
        
        return assessment
    
    def _get_risk_level(self, score: float) -> str:
        """Convert numerical risk score to descriptive level"""
        if score < 20:
            return "very_low"
        elif score < 40:
            return "low"
        elif score < 60:
            return "moderate"
        elif score < 80:
            return "high"
        else:
            return "very_high"


if __name__ == "__main__":
    # Simple test
    risk_manager = RiskManager("TestTrader")
    
    print("Risk Manager Test:")
    print(f"Risk Limits: {risk_manager.get_risk_summary()}")
    
    # Test validation
    is_valid, msg = risk_manager.validate_trade("AAPL", 5, 150.0, 10000.0, 2)
    print(f"Trade validation: {is_valid} - {msg}")