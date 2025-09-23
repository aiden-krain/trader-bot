"""
Pydantic models for account-related MCP tool responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from decimal import Decimal

class Position(BaseModel):
    """Model for a single position in the portfolio"""
    symbol: str = Field(description="Stock ticker symbol")
    qty: float = Field(description="Number of shares held")
    side: str = Field(description="Position side (long/short)")
    market_value: float = Field(description="Current market value of position")
    avg_entry_price: float = Field(description="Average entry price per share")
    current_price: float = Field(description="Current market price per share")
    unrealized_pl: float = Field(description="Unrealized profit/loss in dollars")
    unrealized_plpc: float = Field(description="Unrealized profit/loss percentage")
    cost_basis: float = Field(description="Total cost basis of position")

class RiskLimits(BaseModel):
    """Model for risk management limits"""
    max_position_size: float = Field(description="Maximum position size in dollars")
    max_portfolio_risk: float = Field(description="Maximum portfolio risk percentage")
    max_daily_trades: int = Field(description="Maximum trades allowed per day")

class AccountInfo(BaseModel):
    """Model for basic account information"""
    trader: str = Field(description="Trader name")
    cash: float = Field(description="Available cash balance")
    portfolio_value: float = Field(description="Total portfolio value")
    buying_power: float = Field(description="Available buying power")
    paper_trading: bool = Field(description="Whether in paper trading mode")

class PortfolioSummary(BaseModel):
    """Model for comprehensive portfolio summary"""
    trader: str = Field(description="Trader name")
    cash: float = Field(description="Available cash balance")
    portfolio_value: float = Field(description="Total portfolio value")
    buying_power: float = Field(description="Available buying power")
    positions_count: int = Field(description="Number of active positions")
    positions: List[Position] = Field(description="List of current positions")
    paper_trading: bool = Field(description="Whether in paper trading mode")

class PortfolioReport(BaseModel):
    """Model for detailed portfolio report"""
    trader: str = Field(description="Trader name")
    cash_balance: float = Field(description="Current cash balance")
    portfolio_value: float = Field(description="Total portfolio value")
    total_pl: float = Field(description="Total profit/loss in dollars")
    total_pl_percent: float = Field(description="Total profit/loss percentage")
    positions_count: int = Field(description="Number of holdings")
    positions_summary: str = Field(description="Summary of current positions")

class TradingGuidance(BaseModel):
    """Model for trading guidance information"""
    trader: str = Field(description="Trader name")
    portfolio_value: float = Field(description="Current portfolio value")
    available_for_trading: float = Field(description="Available funds for trading")
    risk_limits: RiskLimits = Field(description="Current risk limits")
    positions_summary: str = Field(description="Summary of current positions")

class RiskStatus(BaseModel):
    """Model for risk management status"""
    trader: str = Field(description="Trader name")
    risk_limits: Dict[str, Any] = Field(description="Current risk limits")
    portfolio_value: float = Field(description="Current portfolio value")
    status: str = Field(description="Risk status")

class TradingStatus(BaseModel):
    """Model for overall trading system status"""
    paper_trading: bool = Field(description="Whether system is in paper trading mode")
    execute_real_orders: bool = Field(description="Whether real orders are enabled")
    server_status: str = Field(description="Server status")
    active_traders: int = Field(description="Number of active traders")
    risk_management: str = Field(description="Risk management status")
