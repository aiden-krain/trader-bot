"""
Simple Trading Strategies Package

Dead simple strategy system for trading agents. Perfect for new developers!

Available Strategies:
- Warren: Value-oriented long-term investing
- Ray: Systematic diversified approach  
- Cathie: Disruptive innovation focus

Usage:
    from strategies import Warren, Ray, Cathie
    
    # Create strategies directly
    warren = Warren(max_position_size=1500)
    instructions = warren.get_instructions()
    risk_limits = warren.get_risk_limits()
    
    # Or use convenience function
    from strategies import create_strategy
    ray = create_strategy("Ray", max_position_size=800)
"""

# STRATEGY SYSTEM - All you need!
from .strategies import (
    Strategy,
    Warren,
    Ray, 
    Cathie,
    create_strategy,
    list_strategies
)

__all__ = [
    'Strategy',
    'Warren',
    'Ray',
    'Cathie', 
    'create_strategy',
    'list_strategies'
]

# Package metadata
__version__ = "2.0.0"  # Bumped for simplified system
__author__ = "Trader Bot Team"
__description__ = "Simple trading strategy system for AI agents"
