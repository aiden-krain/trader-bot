"""
Account MCP Server - Focused on account information and portfolio management.
Provides comprehensive account data, portfolio analysis, and order history using AccountClient.
Trader-specific server that maintains individual trader contexts and strategies.
"""

import os
import sys

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from core.alpaca_client import AlpacaClient
from utils.database import write_log
from dotenv import load_dotenv

# Import Pydantic models for structured responses
from models import (
    TradingGuidance, PortfolioSummary, PortfolioReport, RiskStatus, 
    Position, RiskLimits, OrderList, Order, TradeList, TradeInfo
)

# Import strategy system
try:
    from strategies import create_strategy, list_strategies
    STRATEGY_SYSTEM_AVAILABLE = True
except ImportError:
    STRATEGY_SYSTEM_AVAILABLE = False
    # Fallback to AlpacaClient strategies
    from core.alpaca_client import warren_strategy, ray_strategy, cathie_strategy

load_dotenv()

mcp = FastMCP("Account Server")

# Trading mode configuration
paper_trading = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"

# Simple cache for trader clients
_trader_clients = {}

# Strategy mapping (fallback only)
if not STRATEGY_SYSTEM_AVAILABLE:
    TRADER_STRATEGIES = {
        "Warren": warren_strategy,
        "Ray": ray_strategy,
        "Cathie": cathie_strategy
    }

def get_trader_client(name: str) -> AlpacaClient:
    """Get or create trader-specific AlpacaClient with strategy injection"""
    if name not in _trader_clients:
        _trader_clients[name] = AlpacaClient(paper_trading=paper_trading, trader_name=name)
    return _trader_clients[name]

@mcp.tool()
async def get_account_info(name: str) -> TradingGuidance:
    """Get comprehensive account information with trading guidance using AccountClient"""
    try:
        client = get_trader_client(name)
        guidance_text = client.get_trading_guidance()
        
        # Extract structured data from AccountClient
        account_info = client.account.get_account_info()
        risk_summary = client.risk_manager.get_risk_summary()
        
        return TradingGuidance(
            trader=name,
            portfolio_value=float(account_info.get('portfolio_value', 0)),
            available_for_trading=float(account_info.get('buying_power', 0)),
            risk_limits=RiskLimits(
                max_position_size=float(risk_summary.get('max_position_size', '$1,000.00').replace('$', '').replace(',', '')),
                max_portfolio_risk=float(risk_summary.get('max_portfolio_risk', '2.0%').replace('%', '')) / 100,
                max_daily_trades=int(risk_summary.get('max_daily_trades', 10))
            ),
            positions_summary=guidance_text
        )
    except Exception as e:
        error_msg = f"❌ Account info error: {str(e)}"
        write_log(name, "error", error_msg)
        # Return default structure with error info
        return TradingGuidance(
            trader=name,
            portfolio_value=0.0,
            available_for_trading=0.0,
            risk_limits=RiskLimits(
                max_position_size=1000.0,
                max_portfolio_risk=0.02,
                max_daily_trades=10
            ),
            positions_summary=error_msg
        )

@mcp.tool()
async def get_trading_guidance(name: str) -> TradingGuidance:
    """Get comprehensive trading guidance using AccountClient and RiskManager"""
    try:
        client = get_trader_client(name)
        guidance_text = client.get_trading_guidance()
        
        # Extract structured data from AccountClient
        account_info = client.account.get_account_info()
        risk_summary = client.risk_manager.get_risk_summary()
        
        return TradingGuidance(
            trader=name,
            portfolio_value=float(account_info.get('portfolio_value', 0)),
            available_for_trading=float(account_info.get('buying_power', 0)),
            risk_limits=RiskLimits(
                max_position_size=float(risk_summary.get('max_position_size', '$1,000.00').replace('$', '').replace(',', '')),
                max_portfolio_risk=float(risk_summary.get('max_portfolio_risk', '2.0%').replace('%', '')) / 100,
                max_daily_trades=int(risk_summary.get('max_daily_trades', 10))
            ),
            positions_summary=guidance_text
        )
    except Exception as e:
        error_msg = f"❌ Trading guidance error: {str(e)}"
        write_log(name, "error", error_msg)
        return TradingGuidance(
            trader=name,
            portfolio_value=0.0,
            available_for_trading=0.0,
            risk_limits=RiskLimits(
                max_position_size=1000.0,
                max_portfolio_risk=0.02,
                max_daily_trades=10
            ),
            positions_summary=error_msg
        )

@mcp.tool()
async def get_portfolio_summary(name: str) -> PortfolioSummary:
    """Get portfolio summary with positions and account data using AccountClient"""
    try:
        client = get_trader_client(name)
        account_info = client.account.get_account_info()
        positions_data = client.account.get_positions()
        
        # Convert positions to structured format
        positions = []
        for pos in positions_data:
            if isinstance(pos, dict):
                positions.append(Position(
                    symbol=pos.get('symbol', ''),
                    qty=float(pos.get('qty', 0)),
                    side=pos.get('side', 'long'),
                    market_value=float(pos.get('market_value', 0)),
                    avg_entry_price=float(pos.get('avg_entry_price', 0)),
                    current_price=float(pos.get('current_price', 0)),
                    unrealized_pl=float(pos.get('unrealized_pl', 0)),
                    unrealized_plpc=float(pos.get('unrealized_plpc', 0)),
                    cost_basis=float(pos.get('cost_basis', 0))
                ))
        
        return PortfolioSummary(
            trader=name,
            cash=float(account_info.get('cash', 0)),
            portfolio_value=float(account_info.get('portfolio_value', 0)),
            buying_power=float(account_info.get('buying_power', 0)),
            positions_count=len(positions),
            positions=positions,
            paper_trading=paper_trading
        )
    except Exception as e:
        write_log(name, "error", f"Portfolio summary error: {str(e)}")
        return PortfolioSummary(
            trader=name,
            cash=0.0,
            portfolio_value=0.0,
            buying_power=0.0,
            positions_count=0,
            positions=[],
            paper_trading=paper_trading
        )

@mcp.tool()
async def get_portfolio_report(name: str) -> PortfolioReport:
    """Get detailed portfolio report using AccountClient"""
    try:
        client = get_trader_client(name)
        report_text = client.get_portfolio_report()
        account_info = client.account.get_account_info()
        positions = client.account.get_positions()
        
        # Calculate P&L from positions
        total_pl = sum(float(pos.get('unrealized_pl', 0)) for pos in positions if isinstance(pos, dict))
        portfolio_value = float(account_info.get('portfolio_value', 0))
        total_pl_percent = (total_pl / portfolio_value * 100) if portfolio_value > 0 else 0
        
        return PortfolioReport(
            trader=name,
            cash_balance=float(account_info.get('cash', 0)),
            portfolio_value=portfolio_value,
            total_pl=total_pl,
            total_pl_percent=total_pl_percent,
            positions_count=len(positions),
            positions_summary=report_text
        )
    except Exception as e:
        error_msg = f"❌ Portfolio report error: {str(e)}"
        write_log(name, "error", error_msg)
        return PortfolioReport(
            trader=name,
            cash_balance=0.0,
            portfolio_value=0.0,
            total_pl=0.0,
            total_pl_percent=0.0,
            positions_count=0,
            positions_summary=error_msg
        )

@mcp.tool()
async def get_current_orders(name: str) -> OrderList:
    """Get all current open orders for a trader using AccountClient. Essential before making new trades."""
    try:
        client = get_trader_client(name)
        
        # Use AccountClient's get_orders method with status="all"
        orders_data = client.account.get_orders(status="all", limit=50)
        
        orders = []
        for order_data in orders_data:
            orders.append(Order(
                id=order_data.get('id', ''),
                symbol=order_data.get('symbol', ''),
                side=order_data.get('side', 'unknown'),
                qty=order_data.get('qty', 0),
                order_type=order_data.get('order_type', 'market'),
                limit_price=order_data.get('limit_price'),
                filled_qty=order_data.get('filled_qty', 0),
                filled_avg_price=order_data.get('avg_fill_price'),
                status=order_data.get('status', 'open'),
                paper_trading=client.paper_trading
            ))
        
        return OrderList(
            orders=orders,
            total_count=len(orders),
            status_filter="open",
            paper_trading=client.paper_trading
        )
        
    except Exception as e:
        error_msg = f"❌ Get current orders error: {str(e)}"
        write_log(name, "error", error_msg)
        return OrderList(
            orders=[],
            total_count=0,
            status_filter="open",
            paper_trading=True
        )

@mcp.tool()
async def get_recent_trades(name: str, days: int = 3) -> TradeList:
    """Get recent completed trades for a trader using AccountClient to learn from performance."""
    try:
        client = get_trader_client(name)
        
        # Use AccountClient's get_orders method with status="filled"
        orders_data = client.account.get_orders(status="filled", limit=20)
        
        trades = []
        for order_data in orders_data:
            filled_avg_price = order_data.get('avg_fill_price')
            if filled_avg_price:  # Only include actually filled orders
                trades.append(TradeInfo(
                    symbol=order_data.get('symbol', ''),
                    side=order_data.get('side', 'unknown'),
                    quantity=order_data.get('filled_qty', order_data.get('qty', 0)),
                    price=float(filled_avg_price),
                    timestamp=order_data.get('filled_at'),
                    order_id=order_data.get('id')
                ))
        
        return TradeList(
            trades=trades,
            total_count=len(trades),
            period_days=days,
            paper_trading=client.paper_trading
        )
        
    except Exception as e:
        error_msg = f"❌ Get recent trades error: {str(e)}"
        write_log(name, "error", error_msg)
        return TradeList(
            trades=[],
            total_count=0,
            period_days=days,
            paper_trading=True
        )

@mcp.tool()
async def get_risk_status(name: str) -> RiskStatus:
    """Get current risk management status using RiskManager"""
    try:
        client = get_trader_client(name)
        risk_summary = client.risk_manager.get_risk_summary()
        portfolio_value = client.calculate_portfolio_value()
        
        return RiskStatus(
            trader=name,
            risk_limits=risk_summary,
            portfolio_value=portfolio_value,
            status="active"
        )
    except Exception as e:
        write_log(name, "error", f"Risk status error: {str(e)}")
        return RiskStatus(
            trader=name,
            risk_limits={},
            portfolio_value=0.0,
            status="error"
        )

@mcp.tool()
async def get_strategy(name: str) -> str:
    """Get investment strategy for a trader using Strategy system"""
    try:
        if STRATEGY_SYSTEM_AVAILABLE:
            # Use simple strategy system
            strategy_obj = create_strategy(name)
            return strategy_obj.get_instructions()
        else:
            # Fallback to old system
            strategy = TRADER_STRATEGIES.get(name)
            if strategy:
                return strategy.strip()
            else:
                return f"No strategy found for trader {name}. Available traders: {', '.join(TRADER_STRATEGIES.keys())}"
    except Exception as e:
        error_msg = f"❌ Strategy retrieval error: {str(e)}"
        write_log(name, "error", error_msg)
        return error_msg

# Resource endpoints for account information
@mcp.resource("accounts://trader/{name}")
async def read_trader_resource(name: str) -> str:
    """Get trader account information as resource"""
    try:
        client = get_trader_client(name)
        return client.get_trading_guidance()
    except Exception as e:
        return f"❌ Error loading trader {name}: {str(e)}"

@mcp.resource("accounts://strategy/{name}")
async def read_strategy_resource(name: str) -> str:
    """Get trader investment strategy as resource"""
    try:
        if STRATEGY_SYSTEM_AVAILABLE:
            # Use simple strategy system
            strategy_obj = create_strategy(name)
            return strategy_obj.get_instructions()
        else:
            # Fallback to old system
            strategy = TRADER_STRATEGIES.get(name)
            if strategy:
                return strategy.strip()
            else:
                return f"No strategy found for trader {name}. Available traders: {', '.join(TRADER_STRATEGIES.keys())}"
    except Exception as e:
        return f"❌ Error loading strategy for {name}: {str(e)}"

if __name__ == "__main__":
    print(f"🚀 Starting Account MCP Server")
    print(f"   Paper Trading: {paper_trading}")
    print(f"   Focus: Account Info & Portfolio Management")
    
    mcp.run(transport="stdio")
