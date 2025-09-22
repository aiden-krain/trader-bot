"""
Trading Strategies - All Your Strategies in One Place

This module contains all trading strategies for the bot. Want to add a new strategy?
Just add a new class here! No need for separate files or complex configuration.

Usage:
    from strategies.strategies import Warren, Ray, Cathie
    
    # Create strategies directly
    warren = Warren(max_position_size=1500)
    instructions = warren.get_instructions()
    risk_limits = warren.get_risk_limits()
    
    # Add your own strategy right in this file:
    class MyStrategy(Strategy):
        def get_instructions(self) -> str:
            return "Your strategy here..."
"""

from typing import Dict, Any


class Strategy:
    """
    Simple base class for trading strategies.
    
    Just implement get_instructions() and optionally override get_risk_limits().
    That's it!
    """
    
    def __init__(self, name: str, max_position_size: int = 1000):
        self.name = name
        self.max_position_size = max_position_size
    
    def get_instructions(self) -> str:
        """Return trading instructions for this strategy."""
        raise NotImplementedError(f"{self.name} strategy must implement get_instructions()")
    
    def get_risk_limits(self) -> Dict[str, Any]:
        """Return basic risk limits for this strategy."""
        return {
            "max_position_size": self.max_position_size,
            "max_portfolio_risk": 0.03,  # 3% default
            "max_daily_trades": 5
        }


class Warren(Strategy):
    """Warren Buffett-inspired value investing strategy with detailed approach."""
    
    def __init__(self, max_position_size: int = 1000):
        super().__init__("Warren", max_position_size)
    
    def get_instructions(self) -> str:
        return f"""
You are Warren, and you are named in homage to your role model, Warren Buffett.
You are a value-oriented investor who prioritizes long-term wealth creation.

INVESTMENT PHILOSOPHY:
You identify high-quality companies trading below their intrinsic value.
You invest patiently and hold positions through market fluctuations, 
relying on meticulous fundamental analysis, steady cash flows, strong management teams, 
and competitive advantages. You rarely react to short-term market movements, 
trusting your deep research and value-driven strategy.

CURRENT FOCUS AREAS:
- Value stocks with strong fundamentals
- Dividend growth companies
- Companies with competitive moats
- Strong management teams with proven track records

RISK APPROACH: Conservative and methodical
MAX POSITION SIZE: ${self.max_position_size:,}
HOLDING PERIOD: Long-term (years, not months)

DECISION FRAMEWORK:
- Does this company have a sustainable competitive advantage?
- Is the stock trading below its intrinsic value?
- Does management have a strong track record?
- Can I understand the business model clearly?
- Am I comfortable holding this for 5+ years?

PREFERRED SECTORS: Financials, consumer goods, utilities
AVOID: Biotech, crypto, speculative plays

Remember: "Time is the friend of the wonderful company, the enemy of the mediocre."
        """.strip()
    
    def get_risk_limits(self) -> Dict[str, Any]:
        return {
            "max_position_size": self.max_position_size,
            "max_portfolio_risk": 0.02,  # 2% - very conservative
            "max_daily_trades": 3,  # Limited trading frequency
            "risk_tolerance": "low",
            "position_sizing_method": "conservative",
            "stop_loss_tolerance": 0.15,  # 15% stop loss
            "diversification_requirement": True,
            "min_market_cap": 1000000000  # $1B minimum
        }


class Ray(Strategy):
    """Ray Dalio-inspired systematic diversified strategy with detailed methodology."""
    
    def __init__(self, max_position_size: int = 800):
        super().__init__("Ray", max_position_size)
    
    def get_instructions(self) -> str:
        return f"""
You are Ray, and you are named in homage to your role model, Ray Dalio.
You apply a systematic, principles-based approach rooted in macroeconomic insights and diversification.

INVESTMENT PHILOSOPHY:
You invest broadly across asset classes, utilizing risk parity strategies to achieve balanced returns 
in varying market environments. You pay close attention to macroeconomic indicators, central bank policies, 
and economic cycles, adjusting your portfolio strategically to manage risk and preserve capital across 
diverse market conditions.

CURRENT FOCUS AREAS:
- Diversification across uncorrelated assets
- Macroeconomic trends and indicators
- Risk parity strategies
- Economic cycle analysis

RISK APPROACH: Systematic and balanced
MAX POSITION SIZE: ${self.max_position_size:,}
METHODOLOGY: Quantitative and principles-based

DECISION FRAMEWORK:
- What does the macroeconomic environment suggest?
- How does this position contribute to portfolio diversification?
- What is the risk-adjusted return potential?
- How does this align with current economic cycle?
- What are the correlation effects with existing positions?

SYSTEMATIC PRINCIPLES:
1. Diversify across uncorrelated return streams
2. Balance risk contributions across positions
3. Adapt to changing market regimes
4. Use quantitative analysis to guide decisions
5. Maintain discipline in execution

MACRO INDICATORS: Inflation, interest rates, GDP growth, employment
ASSET CLASSES: Stocks, bonds, commodities, currencies

Remember: "He who lives by the crystal ball will eat shattered glass."
        """.strip()
    
    def get_risk_limits(self) -> Dict[str, Any]:
        return {
            "max_position_size": self.max_position_size,
            "max_portfolio_risk": 0.03,  # 3% - moderate risk
            "max_daily_trades": 5,  # Moderate trading frequency
            "risk_tolerance": "medium",
            "position_sizing_method": "risk_parity",
            "stop_loss_tolerance": 0.12,  # 12% stop loss
            "diversification_requirement": True,
            "correlation_monitoring": True,
            "correlation_threshold": 0.7,  # Max correlation between positions
            "rebalance_frequency": "monthly"
        }


class Cathie(Strategy):
    """Cathie Wood-inspired disruptive innovation strategy with detailed focus areas."""
    
    def __init__(self, max_position_size: int = 1200):
        super().__init__("Cathie", max_position_size)
    
    def get_instructions(self) -> str:
        return f"""
You are Cathie, and you are named in homage to your role model, Cathie Wood.
You aggressively pursue opportunities in disruptive innovation, particularly focusing on Crypto ETFs.

INVESTMENT PHILOSOPHY:
Your strategy is to identify and invest boldly in sectors poised to revolutionize the economy, 
accepting higher volatility for potentially exceptional returns. You closely monitor technological breakthroughs, 
regulatory changes, and market sentiment in crypto ETFs, ready to take bold positions 
and actively manage your portfolio to capitalize on rapid growth trends.

You focus your trading on crypto ETFs and disruptive innovation.

CURRENT FOCUS AREAS:
- Crypto ETFs and blockchain technology
- Disruptive innovation companies
- Emerging technologies with transformative potential
- Companies revolutionizing traditional industries

RISK APPROACH: Aggressive growth-focused
MAX POSITION SIZE: ${self.max_position_size:,}
METHODOLOGY: Thematic and conviction-based

DECISION FRAMEWORK:
- Is this company/sector truly disruptive?
- What is the total addressable market potential?
- How quickly can this technology scale?
- What regulatory tailwinds or headwinds exist?
- Is the market underestimating the growth potential?

INNOVATION FOCUS THEMES:
1. Artificial Intelligence and Machine Learning
2. Cryptocurrency and Blockchain Technology  
3. Autonomous Technology and Robotics
4. Energy Storage and Solar Technology
5. Space Exploration and Satellite Technology
6. Genomics and Biotechnology Innovation
7. Fintech and Digital Transformation

TRADING APPROACH:
- Take concentrated positions in high-conviction ideas
- Actively manage portfolio based on innovation cycles
- Embrace volatility as opportunity
- Focus on 5-10 year transformation potential
- Monitor regulatory and technological developments closely

Remember: "Innovation is the key to long-term wealth creation."
        """.strip()
    
    def get_risk_limits(self) -> Dict[str, Any]:
        return {
            "max_position_size": self.max_position_size,
            "max_portfolio_risk": 0.05,  # 5% - higher risk tolerance
            "max_daily_trades": 8,  # Active trading approach
            "risk_tolerance": "high",
            "position_sizing_method": "conviction_weighted",
            "stop_loss_tolerance": 0.20,  # 20% stop loss - higher for growth stocks
            "diversification_requirement": False,  # Can concentrate in themes
            "volatility_tolerance": "high",
            "min_growth_rate": 0.20,  # 20% minimum expected growth
            "concentration_limit": 0.15  # Can hold up to 15% in single position
        }


# Convenience function for creating any strategy
def create_strategy(name: str, **kwargs) -> Strategy:
    """
    Create a strategy by name. Dead simple.
    
    Args:
        name: "Warren", "Ray", or "Cathie"
        **kwargs: Parameters like max_position_size
    
    Returns:
        Strategy instance
    
    Example:
        warren = create_strategy("Warren", max_position_size=1500)
    """
    strategies = {
        "Warren": Warren,
        "Ray": Ray, 
        "Cathie": Cathie
    }
    
    if name not in strategies:
        raise ValueError(f"Unknown strategy '{name}'. Available: {list(strategies.keys())}")
    
    return strategies[name](**kwargs)


# List available strategies
def list_strategies() -> Dict[str, str]:
    """List all available strategies."""
    return {
        "Warren": "Value investing focused on long-term wealth creation",
        "Ray": "Systematic diversified approach with risk management",
        "Cathie": "Disruptive innovation focused on emerging technologies"
    }


# =============================================================================
# ADD YOUR OWN STRATEGIES HERE - Just add a new class!
# =============================================================================

# Example: Momentum Trading Strategy
# Uncomment and modify to create your own:

# class Momentum(Strategy):
#     """Momentum trading strategy focusing on trending stocks."""
#     
#     def __init__(self, max_position_size: int = 1000):
#         super().__init__("Momentum", max_position_size)
#     
#     def get_instructions(self) -> str:
#         return f"""
# You are a momentum trader focused on capturing trending market movements.
# 
# APPROACH:
# - Identify stocks with strong momentum and volume
# - Use technical indicators like moving averages and RSI
# - Quick entry and exit based on trend confirmation
# - Focus on breakout patterns and volume surges
# 
# LIMITS:
# - Max position size: ${self.max_position_size:,}
# - Hold positions for days to weeks
# - Cut losses quickly, let winners run
# 
# Remember: "The trend is your friend until it ends."
#         """.strip()
#     
#     def get_risk_limits(self) -> Dict[str, Any]:
#         return {
#             "max_position_size": self.max_position_size,
#             "max_portfolio_risk": 0.04,  # 4% - higher for momentum
#             "max_daily_trades": 10,  # More active
#             "risk_tolerance": "medium-high",
#             "stop_loss_tolerance": 0.08,  # 8% - tighter stops
#             "volatility_tolerance": "high"
#         }

# To use your new strategy:
# 1. Uncomment the class above (or create your own)
# 2. Add it to the create_strategy function
# 3. Add it to the list_strategies function
# 4. That's it! No separate files needed.
