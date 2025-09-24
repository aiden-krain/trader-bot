"""
Enhanced Gradio dashboard for AI Trading Bot with portfolio tracking and visualization.
This is the standalone dashboard version (without background trading bot).
"""
import gradio as gr
from utils.util import css, js, Color
import pandas as pd
from trading_floor import names, lastnames, short_model_names
import plotly.express as px
from trading_core.alpaca_client import AlpacaClient
from utils.database import read_log, write_portfolio_snapshot, read_portfolio_history, read_all_portfolio_history, read_recent_logs
import json
from datetime import datetime
import time

mapper = {
    "trace": Color.WHITE,
    "agent": Color.CYAN,
    "function": Color.GREEN,
    "generation": Color.YELLOW,
    "response": Color.MAGENTA,
    "account": Color.RED,
}


# =============================================================================
# Portfolio Tracking and Enhanced UI Functions
# =============================================================================

def log_portfolio_snapshots():
    """Collect and log portfolio snapshots for all traders"""
    try:
        snapshots_logged = 0
        for trader_name in ["warren", "ray", "cathie"]:
            try:
                # Create AlpacaClient instance for each trader
                client = AlpacaClient(paper_trading=True, trader_name=trader_name)
                
                # Get portfolio data
                account_info = client.account.get_account_info()
                positions = client.account.get_positions()
                
                # Calculate total P&L
                total_pl = sum(float(pos.get('unrealized_pl', 0)) for pos in positions if isinstance(pos, dict))
                
                # Log portfolio snapshot
                write_portfolio_snapshot(
                    trader=trader_name,
                    portfolio_value=float(account_info.get('portfolio_value', 0)),
                    cash=float(account_info.get('cash', 0)),
                    positions_count=len(positions),
                    total_pl=total_pl
                )
                snapshots_logged += 1
                
            except Exception as trader_error:
                print(f"Portfolio snapshot error for {trader_name}: {trader_error}")
                continue
        
        return f"✅ Portfolio snapshots logged for {snapshots_logged} traders"
    except Exception as e:
        return f"❌ Portfolio snapshot error: {str(e)}"

def create_portfolio_chart(days=30):
    """Create interactive portfolio value chart"""
    try:
        # Get data using our new database functions
        all_history = read_all_portfolio_history(days=days)
        
        # Convert to DataFrame for Plotly
        chart_data = []
        for trader, history in all_history.items():
            for snapshot in history:
                chart_data.append({
                    'Date': snapshot['timestamp'],
                    'Portfolio Value': snapshot['portfolio_value'],
                    'Trader': snapshot['trader'],
                    'Cash': snapshot['cash'],
                    'Positions': snapshot['positions_count'],
                    'Total P&L': snapshot['total_pl']
                })
        
        if not chart_data:
            # Create empty chart with message
            fig = px.line(title="📊 Portfolio Value Over Time")
            fig.add_annotation(
                text="No portfolio history available yet.<br>Click 'Log Portfolio Snapshots' to start collecting data.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Portfolio Value ($)",
                height=400
            )
            return fig
        
        df = pd.DataFrame(chart_data)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Create interactive line chart
        fig = px.line(
            df, 
            x='Date', 
            y='Portfolio Value',
            color='Trader',
            title='📊 Portfolio Value Over Time',
            hover_data=['Cash', 'Positions', 'Total P&L'],
            color_discrete_map={
                'Warren': '#2E8B57',  # Sea Green
                'Ray': '#4169E1',     # Royal Blue  
                'Cathie': '#DC143C'   # Crimson
            }
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            hovermode='x unified',
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Format hover template
        fig.update_traces(
            hovertemplate="<b>%{fullData.name}</b><br>" +
                         "Date: %{x}<br>" +
                         "Portfolio Value: $%{y:,.2f}<br>" +
                         "Cash: $%{customdata[0]:,.2f}<br>" +
                         "Positions: %{customdata[1]}<br>" +
                         "Total P&L: $%{customdata[2]:,.2f}<extra></extra>"
        )
        
        return fig
    except Exception as e:
        # Error chart
        fig = px.line(title=f"Chart Error: {str(e)}")
        fig.add_annotation(
            text=f"Error loading chart: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="red")
        )
        return fig

def get_recent_orders_data():
    """Get recent orders for all traders using existing MCP tools"""
    try:
        all_orders = []
        
        for trader_name in ["warren", "ray", "cathie"]:
            try:
                # Create AlpacaClient instance for each trader
                client = AlpacaClient(paper_trading=True, trader_name=trader_name)
                
                # Get recent filled orders (trades)
                orders_data = client.account.get_orders(status="filled", limit=10)
                
                for order_data in orders_data:
                    filled_avg_price = order_data.get('filled_avg_price')
                    if filled_avg_price:  # Only include actually filled orders
                        all_orders.append({
                            'Trader': trader_name.title(),
                            'Symbol': order_data.get('symbol', ''),
                            'Side': order_data.get('side', '').upper(),
                            'Quantity': float(order_data.get('filled_qty', 0)),
                            'Price': f"${float(filled_avg_price):.2f}",
                            'Timestamp': order_data.get('filled_at', ''),
                            'Order ID': order_data.get('id', '')[:8] + '...' if order_data.get('id') else 'N/A'
                        })
                        
            except Exception as trader_error:
                print(f"Orders data error for {trader_name}: {trader_error}")
                continue
        
        if not all_orders:
            # Return empty DataFrame with message
            return pd.DataFrame({
                'Message': ['No recent orders available yet. Orders will appear after trading activity.'],
                'Trader': [''],
                'Symbol': [''],
                'Side': [''],
                'Quantity': [''],
                'Price': [''],
                'Timestamp': ['']
            })
        
        # Sort by timestamp (most recent first)
        all_orders.sort(key=lambda x: x['Timestamp'], reverse=True)
        
        # Return last 10 orders
        return pd.DataFrame(all_orders[:10])
    
    except Exception as e:
        return pd.DataFrame({
            'Error': [f'Error loading orders: {str(e)}'],
            'Trader': [''],
            'Symbol': [''],
            'Side': [''],
            'Quantity': [''],
            'Price': [''],
            'Timestamp': ['']
        })

def get_portfolio_chart_data():
    """Get portfolio data for Gradio chart component"""
    return create_portfolio_chart()

def refresh_portfolio_data():
    """Refresh portfolio snapshots and return updated chart"""
    log_result = log_portfolio_snapshots()
    chart = create_portfolio_chart()
    orders = get_recent_orders_data()
    return chart, orders, log_result

def get_logs():
    """Get recent trading logs using enhanced database functions"""
    try:
        # Use the enhanced read_recent_logs function
        all_logs = read_recent_logs(trader=None, log_types=None, limit=20)
        
        if all_logs:
            log_text = ""
            for log in all_logs[:15]:  # Show last 15 entries
                trader = log['trader']
                timestamp = log['timestamp']
                message = log['message']
                log_text += f"**{timestamp} - {trader}:** {message}\n\n"
            return log_text if log_text else "No recent logs available"
        else:
            return "No logs available yet - logs will appear after trading activity"
    except Exception as e:
        return f"Error loading logs: {str(e)}"

class TraderView:
    """UI wrapper for Trader class - handles dashboard display logic"""
    
    def __init__(self, trader_name: str, lastname: str, model_name: str):
        self.name = trader_name
        self.lastname = lastname
        self.model_name = model_name
        self.client = AlpacaClient(paper_trading=True, trader_name=trader_name)
        self.account_data = None
        self.positions = []
        self.reload()

    def reload(self):
        """Refresh trader data"""
        try:
            self.account_data = self.client.account.get_account_info()
            self.positions = self.client.account.get_positions()
        except Exception as e:
            print(f"Error loading account data for {self.name}: {e}")
            self.account_data = {"portfolio_value": 0, "cash": 0}
            self.positions = []

    def get_title(self) -> str:
        """Get formatted title for dashboard display"""
        return f"<div style='text-align: center;font-size:34px;'>{self.name}<span style='color:#ccc;font-size:24px;'> ({self.model_name}) - {self.lastname}</span></div>"

    def get_account_info(self) -> str:
        """Get formatted account info for dashboard display"""
        if not self.account_data:
            return "No account data available"
        
        portfolio_value = float(self.account_data.get("portfolio_value", 0))
        cash = float(self.account_data.get("cash", 0))
        
        return f"""
        **Portfolio Value:** ${portfolio_value:,.2f}
        **Cash:** ${cash:,.2f}
        **Positions:** {len(self.positions)}
        """

    def get_positions_df(self) -> pd.DataFrame:
        """Get positions as DataFrame for dashboard display"""
        if not self.positions:
            return pd.DataFrame(columns=["Symbol", "Quantity", "Market Value", "Unrealized P&L"])
        
        positions_data = []
        for pos in self.positions:
            positions_data.append({
                "Symbol": pos.get("symbol", ""),
                "Quantity": float(pos.get("qty", 0)),
                "Market Value": f"${float(pos.get('market_value', 0)):,.2f}",
                "Unrealized P&L": f"${float(pos.get('unrealized_pl', 0)):,.2f}"
            })
        
        return pd.DataFrame(positions_data)


# Enhanced CSS with mobile responsiveness
enhanced_css = css + """
/* Mobile responsiveness enhancements */
@media (max-width: 768px) {
    .gradio-container {
        padding: 10px !important;
    }
    
    .plot-container {
        height: 300px !important;
    }
    
    .dataframe {
        font-size: 12px !important;
        overflow-x: auto !important;
    }
    
    .gr-button {
        width: 100% !important;
        margin: 5px 0 !important;
    }
    
    .gr-row {
        flex-direction: column !important;
    }
    
    .gr-column {
        width: 100% !important;
        margin: 5px 0 !important;
    }
}

/* Enhanced chart styling */
.portfolio-chart {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 10px;
    background: white;
}

.orders-table {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    background: white;
}
"""

# Create trader instances and their UI wrappers
trader_views = [TraderView(name, lastname, model) for name, lastname, model in zip(names, lastnames, short_model_names)]

# Main UI construction
def create_ui():
    """Create the enhanced Gradio UI for the trading dashboard"""
    
    with gr.Blocks(css=enhanced_css, js=js, title="AI Trading Bot Dashboard") as ui:
        gr.HTML("<h1 style='text-align: center; color: #2E8B57;'>🤖 AI Trading Bot - Enhanced Dashboard</h1>")
        
        # Main Tabs Section
        with gr.Tabs():
            # NEW: Portfolio Performance Tab
            with gr.TabItem("📈 Portfolio Performance"):
                gr.HTML("<h2 style='text-align: center; color: #2E8B57;'>Portfolio Value Over Time</h2>")
                
                with gr.Row():
                    with gr.Column():
                        portfolio_chart = gr.Plot(
                            value=get_portfolio_chart_data(),
                            elem_classes=["portfolio-chart"]
                        )
                
                with gr.Row():
                    with gr.Column(scale=2):
                        refresh_portfolio_btn = gr.Button("📊 Log Current Portfolio Snapshots", variant="primary")
                        refresh_chart_btn = gr.Button("🔄 Refresh Chart", variant="secondary")
                    with gr.Column(scale=1):
                        snapshot_status = gr.Markdown("Click 'Log Current Portfolio Snapshots' to collect data for the chart.")
                
                gr.HTML("<h3 style='color: #2E8B57;'>📋 Recent Orders (Last 10)</h3>")
                
                with gr.Row():
                    with gr.Column():
                        orders_table = gr.Dataframe(
                            value=get_recent_orders_data(),
                            headers=['Trader', 'Symbol', 'Side', 'Quantity', 'Price', 'Timestamp', 'Order ID'],
                            elem_classes=["orders-table"],
                            interactive=False
                        )
                
                with gr.Row():
                    refresh_orders_btn = gr.Button("🔄 Refresh Orders", variant="secondary")
                
                # Connect refresh functions
                refresh_portfolio_btn.click(
                    fn=refresh_portfolio_data,
                    outputs=[portfolio_chart, orders_table, snapshot_status]
                )
                refresh_chart_btn.click(
                    fn=get_portfolio_chart_data,
                    outputs=portfolio_chart
                )
                refresh_orders_btn.click(
                    fn=get_recent_orders_data,
                    outputs=orders_table
                )
            
            # Individual trader tabs
            for i, trader_view in enumerate(trader_views):
                with gr.TabItem(f"{trader_view.name} ({trader_view.model_name})"):
                    gr.HTML(trader_view.get_title())
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            account_info = gr.Markdown(trader_view.get_account_info())
                        with gr.Column(scale=2):
                            positions_df = gr.Dataframe(
                                value=trader_view.get_positions_df(),
                                headers=["Symbol", "Quantity", "Market Value", "Unrealized P&L"]
                            )
                    
                    refresh_btn = gr.Button(f"🔄 Refresh {trader_view.name}'s Data", variant="primary")
                    refresh_btn.click(
                        fn=lambda tv=trader_view: (tv.reload(), tv.get_account_info(), tv.get_positions_df())[1:],
                        outputs=[account_info, positions_df]
                    )
            
            # Enhanced Logs Tab
            with gr.TabItem("📋 Trading Logs"):
                gr.HTML("<h3 style='color: #2E8B57;'>Recent Trading Activity</h3>")
                logs_display = gr.Markdown(get_logs())
                refresh_logs_btn = gr.Button("🔄 Refresh Logs", variant="secondary")
                refresh_logs_btn.click(fn=get_logs, outputs=logs_display)

    return ui


if __name__ == "__main__":
    ui = create_ui()
    ui.launch(inbrowser=True)
