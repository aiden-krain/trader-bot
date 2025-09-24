"""
Account Client - Account information and portfolio operations.
Handles account data, positions, and portfolio calculations.
"""

from typing import Dict, Any, List

from .base_alpaca_client import BaseAlpacaClient


class AccountClient(BaseAlpacaClient):
    """
    Simple account client that handles account info and portfolio operations.
    """
    
    def __init__(self, paper_trading: bool = True, trader_name: str = None, shared_connection=None):
        super().__init__(paper_trading, trader_name, shared_connection)
    
    def get_account_info(self) -> Dict:
        """Get comprehensive account information"""
        try:
            account = self.trading_client.get_account()
            return {
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                "status": str(account.status),
                "account_blocked": bool(getattr(account, 'account_blocked', False)),
                "trading_blocked": bool(getattr(account, 'trading_blocked', False)),
                "pattern_day_trader": bool(getattr(account, 'pattern_day_trader', False)),
                "day_trade_count": int(getattr(account, 'day_trade_count', 0)),
                "daytrade_buying_power": float(getattr(account, 'daytrade_buying_power', account.buying_power))
            }
        except Exception as e:
            print(f"Error getting account info: {e}")
            raise e
    
    def get_positions(self) -> List[Dict]:
        """Get all current positions"""
        try:
            positions = self.trading_client.get_all_positions()
            return [{
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "side": "long" if float(pos.qty) > 0 else "short",
                "market_value": float(pos.market_value) if pos.market_value else 0.0,
                "avg_entry_price": float(pos.avg_entry_price) if pos.avg_entry_price else 0.0,
                "current_price": float(pos.current_price) if pos.current_price else 0.0,
                "unrealized_pl": float(pos.unrealized_pl) if pos.unrealized_pl else 0.0,
                "unrealized_plpc": float(pos.unrealized_plpc) if pos.unrealized_plpc else 0.0,
                "cost_basis": float(pos.cost_basis) if pos.cost_basis else 0.0
            } for pos in positions]
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
    
    def calculate_portfolio_value(self) -> float:
        """Calculate current portfolio value using real Alpaca data"""
        try:
            account_info = self.get_account_info()
            return float(account_info.get("portfolio_value", 0))
        except Exception as e:
            print(f"Error calculating portfolio value: {e}")
            raise e
    
    def get_orders(self, status: str = "all", limit: int = 50) -> List[Dict]:
        """Get order history from Alpaca"""
        try:
            from alpaca.trading.requests import GetOrdersRequest
            from alpaca.trading.enums import QueryOrderStatus
            
            # Map status string to enum (only ALL, OPEN, CLOSED are available)
            status_map = {
                "all": QueryOrderStatus.ALL,
                "open": QueryOrderStatus.OPEN, 
                "closed": QueryOrderStatus.CLOSED,
                "filled": QueryOrderStatus.CLOSED,  # Filled orders are in CLOSED status
                "cancelled": QueryOrderStatus.CLOSED  # Cancelled orders are also in CLOSED status
            }
            
            order_status = status_map.get(status.lower(), QueryOrderStatus.ALL)
            
            # Create request
            request = GetOrdersRequest(status=order_status, limit=limit)
            orders = self.trading_client.get_orders(filter=request)
            
            # Convert orders to dict format
            order_dicts = []
            for order in orders:
                order_dict = {
                    "id": str(order.id),
                    "symbol": order.symbol,
                    "qty": int(order.qty) if order.qty else 0,
                    "filled_qty": int(order.filled_qty) if order.filled_qty else 0,
                    "side": str(order.side).lower(),
                    "order_type": str(order.order_type),
                    "status": str(order.status),
                    "submitted_at": str(order.submitted_at) if order.submitted_at else None,
                    "filled_at": str(order.filled_at) if order.filled_at else None,
                    "avg_fill_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                    "time_in_force": str(order.time_in_force) if order.time_in_force else None
                }
                order_dicts.append(order_dict)
            
            return order_dicts
            
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary with positions and account data"""
        try:
            account_info = self.get_account_info()
            positions = self.get_positions()
            
            return {
                "trader": self.trader_name,
                "cash": float(account_info.get('cash', 0)),
                "portfolio_value": float(account_info.get('portfolio_value', 0)),
                "buying_power": float(account_info.get('buying_power', 0)),
                "positions_count": len(positions),
                "positions": positions,
                "paper_trading": self.paper_trading
            }
        except Exception as e:
            print(f"Portfolio summary error: {e}")
            raise e
    
    def get_portfolio_report(self) -> str:
        """Get detailed portfolio report"""
        try:
            account_info = self.get_account_info()
            positions = self.get_positions()
            
            report = f"""📊 ACCOUNT REPORT - {self.trader_name.upper()}
💰 Cash Balance: ${float(account_info.get('cash', 0)):,.2f}
📈 Portfolio Value: ${float(account_info.get('portfolio_value', 0)):,.2f}
📊 Total P&L: ${float(account_info.get('portfolio_value', 0)) - 1000:.2f} ({((float(account_info.get('portfolio_value', 0)) / 1000) - 1) * 100:.1f}%)

🏢 Holdings ({len(positions)} positions):"""
            
            if positions:
                for pos in positions:
                    current_price = float(pos.get('current_price', 0))
                    qty = float(pos['qty'])
                    market_value = current_price * qty
                    report += f"\n  • {pos['symbol']}: {qty} shares @ ${current_price:.2f} = ${market_value:.2f}"
            else:
                report += "\n  No positions currently held"
            
            return report
            
        except Exception as e:
            print(f"Error generating portfolio report: {e}")
            raise e
