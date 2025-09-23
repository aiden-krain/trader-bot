"""
Clean Accounts MCP Server - Direct AlpacaClient Integration.
Provides streamlined trading operations with integrated risk management.
Simple, focused architecture for production trading with structured Pydantic outputs.
"""

import os
import sys
import json

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from core.alpaca_client import AlpacaClient
from utils.database import write_log
from typing import Dict, Any, List
from dotenv import load_dotenv

# Import Pydantic models for structured responses
from models import (
    AccountInfo, PortfolioSummary, PortfolioReport, TradingGuidance, 
    RiskStatus, TradingStatus, TradeResult, StockPrice, Position, RiskLimits,
    OrderCancellation, OrderList, Order, TradeList, TradeInfo
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

mcp = FastMCP("Accounts Server")

# Trading mode configuration
paper_trading = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"
execute_real_orders = os.getenv("EXECUTE_REAL_ORDERS", "false").lower() == "true"

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
    """Get or create trader-specific AlpacaClient"""
    if name not in _trader_clients:
        _trader_clients[name] = AlpacaClient(paper_trading=paper_trading, trader_name=name)
    return _trader_clients[name]

@mcp.tool()
async def buy_shares(name: str, symbol: str, quantity: int, rationale: str) -> TradeResult:
    """Execute buy order with integrated risk management"""
    try:
        client = get_trader_client(name)
        result_text = client.buy_shares_with_risk_management(symbol.upper(), quantity, rationale)
        
        # Parse the text result and create structured response
        success = "✅" in result_text and "❌" not in result_text
        
        return TradeResult(
            success=success,
            action="buy",
            symbol=symbol.upper(),
            quantity=quantity,
            rationale=rationale,
            message=result_text,
            error=None if success else result_text
        )
    except Exception as e:
        error_msg = f"❌ Buy order error: {str(e)}"
        write_log(name, "error", error_msg)
        return TradeResult(
            success=False,
            action="buy",
            symbol=symbol.upper(),
            quantity=quantity,
            rationale=rationale,
            message=error_msg,
            error=str(e)
        )

@mcp.tool()
async def sell_shares(name: str, symbol: str, quantity: int, rationale: str) -> TradeResult:
    """Execute sell order with integrated risk management"""
    try:
        client = get_trader_client(name)
        result_text = client.sell_shares_with_risk_management(symbol.upper(), quantity, rationale)
        
        # Parse the text result and create structured response
        success = "✅" in result_text and "❌" not in result_text
        
        return TradeResult(
            success=success,
            action="sell",
            symbol=symbol.upper(),
            quantity=quantity,
            rationale=rationale,
            message=result_text,
            error=None if success else result_text
        )
    except Exception as e:
        error_msg = f"❌ Sell order error: {str(e)}"
        write_log(name, "error", error_msg)
        return TradeResult(
            success=False,
            action="sell",
            symbol=symbol.upper(),
            quantity=quantity,
            rationale=rationale,
            message=error_msg,
            error=str(e)
        )

@mcp.tool()
async def get_account_info(name: str) -> TradingGuidance:
    """Get comprehensive account information with trading guidance"""
    try:
        client = get_trader_client(name)
        guidance_text = client.get_trading_guidance()
        
        # Extract structured data from the client
        account_info = client.get_account_info()
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
async def get_portfolio_summary(name: str) -> PortfolioSummary:
    """Get portfolio summary with positions and account data"""
    try:
        client = get_trader_client(name)
        account_info = client.get_account_info()
        positions_data = client.get_positions()
        
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
    """Get detailed portfolio report"""
    try:
        client = get_trader_client(name)
        report_text = client.get_portfolio_report()
        account_info = client.get_account_info()
        positions = client.get_positions()
        
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
async def get_real_price(name: str, symbol: str) -> StockPrice:
    """Get real-time price for a symbol"""
    try:
        client = get_trader_client(name)
        price = client.get_real_price(symbol.upper())
        quote = client.get_quote(symbol.upper())
        
        return StockPrice(
            symbol=symbol.upper(),
            price=price,
            bid=quote.get("bid"),
            ask=quote.get("ask"),
            spread=quote.get("ask", 0) - quote.get("bid", 0) if quote.get("ask") and quote.get("bid") else None,
            source="alpaca",
            timestamp="real-time",
            paper_trading=paper_trading
        )
    except Exception as e:
        write_log(name, "error", f"Price lookup error: {str(e)}")
        return StockPrice(
            symbol=symbol.upper(),
            price=0.0,
            source="alpaca",
            timestamp="real-time",
            paper_trading=paper_trading
        )

@mcp.tool()
async def get_trading_guidance(name: str) -> TradingGuidance:
    """Get comprehensive trading guidance"""
    try:
        client = get_trader_client(name)
        guidance_text = client.get_trading_guidance()
        
        # Extract structured data
        account_info = client.get_account_info()
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
async def get_risk_status(name: str) -> RiskStatus:
    """Get current risk management status"""
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
async def get_trading_status() -> TradingStatus:
    """Get overall trading system status"""
    return TradingStatus(
        paper_trading=paper_trading,
        execute_real_orders=execute_real_orders,
        server_status="active",
        active_traders=len(_trader_clients),
        risk_management="enabled"
    )

@mcp.tool()
async def get_strategy(name: str) -> str:
    """Get investment strategy for a trader"""
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

@mcp.tool()
async def cancel_order(name: str, order_id: str, rationale: str) -> OrderCancellation:
    """Cancel a specific order by ID with rationale"""
    try:
        client = get_trader_client(name)
        
        # Use TradingClient's cancel_order_by_id method
        result = client.trading.cancel_order_by_id(order_id, rationale)
        
        return OrderCancellation(
            success=result["success"],
            order_id=result["order_id"],
            symbol=result["symbol"],
            message=result["message"],
            error=result.get("error")
        )
        
    except Exception as e:
        error_msg = f"❌ Cancel order error: {str(e)}"
        write_log(name, "error", error_msg)
        return OrderCancellation(
            success=False,
            order_id=order_id,
            symbol="",
            message=error_msg,
            error=str(e)
        )

@mcp.tool()
async def cancel_all_orders(name: str, rationale: str) -> OrderCancellation:
    """Cancel all open orders with rationale"""
    try:
        client = get_trader_client(name)
        
        # Use TradingClient's cancel_all_orders method
        result = client.trading.cancel_all_orders(rationale)
        
        return OrderCancellation(
            success=result["success"],
            order_id="ALL",
            symbol="MULTIPLE",
            message=result["message"],
            error=result.get("error")
        )
        
    except Exception as e:
        error_msg = f"❌ Cancel all orders error: {str(e)}"
        write_log(name, "error", error_msg)
        return OrderCancellation(
            success=False,
            order_id="ALL",
            symbol="MULTIPLE",
            message=error_msg,
            error=str(e)
        )

@mcp.tool()
async def get_current_orders(name: str) -> OrderList:
    """Get all current open orders for a trader. Essential before making new trades."""
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
    """Get recent completed trades for a trader to learn from performance."""
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

# Resource endpoints (simplified)
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
    print(f"🚀 Starting Accounts MCP Server")
    print(f"   Paper Trading: {paper_trading}")
    print(f"   Real Orders: {execute_real_orders}")
    print(f"   Architecture: Clean & Simple")
    
    mcp.run(transport="stdio")