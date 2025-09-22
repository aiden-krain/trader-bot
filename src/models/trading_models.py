"""
Pydantic models for trading-related MCP tool responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class RiskLevel(str, Enum):
    """Risk level enumeration"""
    VERY_LOW = "very_low"
    LOW = "low" 
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class RiskAssessment(BaseModel):
    """Model for detailed risk assessment"""
    risk_score: int = Field(description="Risk score from 0-100")
    risk_level: RiskLevel = Field(description="Risk level category")
    risk_emoji: str = Field(description="Risk level emoji indicator")
    conviction_level: int = Field(description="Conviction level 1-10")
    suggested_quantity: Optional[int] = Field(None, description="Suggested quantity based on risk")
    warnings: List[str] = Field(default_factory=list, description="Risk warnings")
    suggestions: List[str] = Field(default_factory=list, description="Risk suggestions")

class TradeResult(BaseModel):
    """Model for trade execution result"""
    success: bool = Field(description="Whether trade was successful")
    action: str = Field(description="Trade action (buy/sell)")
    symbol: str = Field(description="Stock ticker symbol")
    quantity: int = Field(description="Number of shares traded")
    price: Optional[float] = Field(None, description="Execution price")
    risk_level: Optional[RiskLevel] = Field(None, description="Trade risk level")
    risk_assessment: Optional[RiskAssessment] = Field(None, description="Detailed risk assessment")
    rationale: str = Field(description="Trade rationale")
    message: str = Field(description="Trade result message")
    portfolio_impact: Optional[Dict[str, Any]] = Field(None, description="Impact on portfolio")
    error: Optional[str] = Field(None, description="Error message if trade failed")

class OrderCancellation(BaseModel):
    """Model for order cancellation result"""
    success: bool = Field(description="Whether cancellation was successful")
    order_id: str = Field(description="Cancelled order ID")
    symbol: str = Field(description="Stock ticker symbol")
    message: str = Field(description="Cancellation result message")
    error: Optional[str] = Field(None, description="Error message if cancellation failed")
