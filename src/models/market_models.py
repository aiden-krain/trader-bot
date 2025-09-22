"""
Pydantic models for market data MCP tool responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class StockPrice(BaseModel):
    """Model for stock price information"""
    symbol: str = Field(description="Stock ticker symbol")
    price: float = Field(description="Current stock price")
    bid: Optional[float] = Field(None, description="Current bid price")
    ask: Optional[float] = Field(None, description="Current ask price")
    spread: Optional[float] = Field(None, description="Bid-ask spread")
    source: str = Field(description="Data source (e.g., 'alpaca')")
    timestamp: Union[float, str] = Field(description="Price timestamp")
    paper_trading: bool = Field(description="Whether in paper trading mode")

class MarketStatus(BaseModel):
    """Model for market status information"""
    is_open: bool = Field(description="Whether market is currently open")
    next_open: Optional[str] = Field(None, description="Next market open time")
    next_close: Optional[str] = Field(None, description="Next market close time")
    timezone: str = Field(default="America/New_York", description="Market timezone")

class Order(BaseModel):
    """Model for order information"""
    id: Optional[str] = Field(None, description="Order ID")
    symbol: str = Field(description="Stock ticker symbol")
    side: str = Field(description="Order side (buy/sell)")
    qty: Union[int, float] = Field(description="Order quantity")
    order_type: str = Field(description="Order type (market/limit)")
    limit_price: Optional[float] = Field(None, description="Limit price if applicable")
    filled_qty: Optional[Union[int, float]] = Field(None, description="Filled quantity")
    filled_avg_price: Optional[float] = Field(None, description="Average fill price")
    status: Optional[str] = Field(None, description="Order status")
    paper_trading: bool = Field(description="Whether in paper trading mode")

class OrderList(BaseModel):
    """Model for list of orders with metadata"""
    orders: List[Order] = Field(description="List of orders")
    total_count: int = Field(description="Total number of orders")
    status_filter: str = Field(description="Status filter applied")
    paper_trading: bool = Field(description="Whether in paper trading mode")

class TradeInfo(BaseModel):
    """Model for individual trade information"""
    symbol: str = Field(description="Stock ticker symbol")
    side: str = Field(description="Trade side (buy/sell)")
    quantity: Union[int, float] = Field(description="Number of shares traded")
    price: float = Field(description="Trade execution price")
    timestamp: Optional[str] = Field(None, description="Trade timestamp")
    order_id: Optional[str] = Field(None, description="Associated order ID")

class TradeList(BaseModel):
    """Model for list of trades with metadata"""
    trades: List[TradeInfo] = Field(description="List of completed trades")
    total_count: int = Field(description="Total number of trades")
    period_days: int = Field(description="Period in days for trade history")
    paper_trading: bool = Field(description="Whether in paper trading mode")

class Bar(BaseModel):
    """Model for a single price bar/candle"""
    timestamp: Union[str, datetime] = Field(description="Bar timestamp")
    open: float = Field(description="Opening price")
    high: float = Field(description="High price")
    low: float = Field(description="Low price")
    close: float = Field(description="Closing price")
    volume: int = Field(description="Trading volume")

class StockBars(BaseModel):
    """Model for historical stock bars/candles"""
    symbol: str = Field(description="Stock ticker symbol")
    timeframe: str = Field(description="Bar timeframe")
    bars: List[Bar] = Field(description="List of price bars")
    paper_trading: bool = Field(description="Whether in paper trading mode")

class PerformanceAnalysis(BaseModel):
    """Model for stock performance analysis"""
    symbol: str = Field(description="Stock ticker symbol")
    period_days: int = Field(description="Analysis period in days")
    first_price: float = Field(description="First price in period")
    last_price: float = Field(description="Last price in period")
    high_price: float = Field(description="Highest price in period")
    low_price: float = Field(description="Lowest price in period")
    total_return_percent: float = Field(description="Total return percentage")
    price_range_percent: float = Field(description="Price range as percentage")
    average_volume: int = Field(description="Average trading volume")
    paper_trading: bool = Field(description="Whether in paper trading mode")
    analysis_timestamp: float = Field(description="Analysis timestamp")

class MarketMover(BaseModel):
    """Model for market mover information"""
    symbol: str = Field(description="Stock ticker symbol")
    current_price: float = Field(description="Current stock price")
    previous_close: float = Field(description="Previous closing price")
    change_percent: float = Field(description="Price change percentage")
    change_dollar: float = Field(description="Price change in dollars")
    paper_trading: bool = Field(description="Whether in paper trading mode")

class AssetInfo(BaseModel):
    """Model for asset information"""
    symbol: str = Field(description="Stock ticker symbol")
    name: Optional[str] = Field(None, description="Company name")
    exchange: Optional[str] = Field(None, description="Exchange")
    tradable: bool = Field(description="Whether asset is tradable")
    marginable: Optional[bool] = Field(None, description="Whether asset is marginable")
    shortable: Optional[bool] = Field(None, description="Whether asset is shortable")
    current_price: Optional[float] = Field(None, description="Current price if available")
    paper_trading: bool = Field(description="Whether in paper trading mode")

class AssetValidation(BaseModel):
    """Model for asset validation result"""
    symbol: str = Field(description="Stock ticker symbol")
    valid: bool = Field(description="Whether symbol is valid")
    tradable: Optional[bool] = Field(None, description="Whether asset is tradable")
    name: Optional[str] = Field(None, description="Company name")
    exchange: Optional[str] = Field(None, description="Exchange")
    marginable: Optional[bool] = Field(None, description="Whether asset is marginable")
    shortable: Optional[bool] = Field(None, description="Whether asset is shortable")
    paper_trading: bool = Field(description="Whether in paper trading mode")
    error: Optional[str] = Field(None, description="Error message if validation failed")
