"""
Combined application that runs both the trading bot and Gradio dashboard
This allows Railway to serve both the web interface and run the trading bot
"""
import asyncio
import threading
import time
from trading_floor import run_trading_cycle
import gradio as gr
from utils.util import css, js, Color
import pandas as pd
from trading_floor import names, lastnames, short_model_names, create_traders
import plotly.express as px
from utils.database import read_log, write_portfolio_snapshot, read_portfolio_history, read_all_portfolio_history, read_recent_logs
from trading_agents.traders import Trader
from core.alpaca_client import AlpacaClient
import json
from datetime import datetime
import os

# Global status tracking
trading_status = {
    "running": False,
    "last_cycle": "Not started",
    "cycles_completed": 0,
    "errors": []
}

def start_trading_bot():
    """Start the trading bot in a background thread with portfolio tracking - matches trading_floor.py"""
    global trading_status
    
    async def run_bot():
        trading_status["running"] = True
        trading_status["last_cycle"] = f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            # Log initial portfolio snapshots
            print("📊 Logging initial portfolio snapshots...")
            log_portfolio_snapshots()
            
            # Import trading_floor configuration for consistency
            from trading_floor import RUN_EVERY_N_MINUTES, USE_MIXED_MODELS, DEFAULT_MODEL_PROVIDER
            
            print(f"🚀 Starting Production Trading System")
            print(f"   Mixed Models: {USE_MIXED_MODELS}")
            print(f"   Default Provider: {DEFAULT_MODEL_PROVIDER}")
            print(f"   Run Interval: {RUN_EVERY_N_MINUTES} minutes")
            print(f"   Active Traders: {len(names)} ({', '.join(names)})")
            
            # Run the same trading loop as trading_floor.py
            await run_every_n_minutes_with_tracking()
        except Exception as e:
            trading_status["errors"].append(f"{datetime.now()}: {str(e)}")
            trading_status["running"] = False
    
    # Run the trading bot in a separate thread
    def run_in_thread():
        asyncio.run(run_bot())
    
    trading_thread = threading.Thread(target=run_in_thread, daemon=True)
    trading_thread.start()
    print("🚀 Trading bot started in background thread")
    print("📊 Portfolio tracking enabled - snapshots will be logged automatically")

async def run_every_n_minutes_with_tracking():
    """Enhanced version of run_every_n_minutes with UI status tracking"""
    global trading_status
    
    # Import interval from trading_floor.py for consistency
    from trading_floor import RUN_EVERY_N_MINUTES
    
    while True:
        try:
            # Update status before cycle
            trading_status["last_cycle"] = f"Running cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Run the same trading cycle as trading_floor.py
            trading_occurred = await run_trading_cycle()
            
            # Update status after cycle
            trading_status["cycles_completed"] += 1
            if trading_occurred:
                trading_status["last_cycle"] = f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                print(f"✅ Trading cycle completed")
                # Log portfolio snapshots after successful trading
                log_portfolio_snapshots()
            else:
                trading_status["last_cycle"] = f"Skipped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (market closed)"
                print(f"⏸️  Skipping trading (next check in {RUN_EVERY_N_MINUTES} minutes)")
            
        except Exception as e:
            error_msg = f"{datetime.now()}: {str(e)}"
            trading_status["errors"].append(error_msg)
            print(f"❌ Trading cycle error: {e}")
            
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)

# Functions will be started at the end of the file after all definitions

# Import the existing Gradio app components
mapper = {
    "trace": Color.WHITE,
    "agent": Color.CYAN,
    "function": Color.GREEN,
    "generation": Color.YELLOW,
    "response": Color.MAGENTA,
    "account": Color.RED,
}

class TraderView:
    """UI wrapper for Trader class - handles dashboard display logic"""
    
    def __init__(self, trader: Trader):
        self.trader = trader
        self.name = trader.name
        self.lastname = trader.lastname
        self.model_name = trader.model_name

    def get_title(self) -> str:
        """Get formatted title for dashboard display"""
        return f"<div style='text-align: center;font-size:34px;'>{self.name}<span style='color:#ccc;font-size:24px;'> ({self.model_name}) - {self.lastname}</span></div>"

    def get_account_info(self) -> str:
        """Get formatted account info for dashboard display"""
        if not hasattr(self.trader, 'account_data') or not self.trader.account_data:
            return "No account data available"
        
        portfolio_value = float(self.trader.account_data.get("portfolio_value", 0))
        cash = float(self.trader.account_data.get("cash", 0))
        
        return f"""
        **Portfolio Value:** ${portfolio_value:,.2f}
        **Cash:** ${cash:,.2f}
        **Positions:** {len(getattr(self.trader, 'positions', []))}
        """

    def get_positions_df(self) -> pd.DataFrame:
        """Get positions as DataFrame for dashboard display"""
        positions = getattr(self.trader, 'positions', [])
        if not positions:
            return pd.DataFrame(columns=["Symbol", "Quantity", "Market Value", "Unrealized P&L"])
        
        positions_data = []
        for pos in positions:
            positions_data.append({
                "Symbol": pos.get("symbol", ""),
                "Quantity": float(pos.get("qty", 0)),
                "Market Value": f"${float(pos.get('market_value', 0)):,.2f}",
                "Unrealized P&L": f"${float(pos.get('unrealized_pl', 0)):,.2f}"
            })
        
        return pd.DataFrame(positions_data)

    def get_recent_orders_df(self) -> pd.DataFrame:
        """Get recent orders for this trader using existing Alpaca client"""
        try:
            # Use the trader's existing alpaca client
            client = AlpacaClient(paper_trading=True, trader_name=self.name)
            orders_data = client.account.get_orders(status="all", limit=10)  # Get ANY status
            
            if not orders_data:
                return pd.DataFrame(columns=["Symbol", "Side", "Quantity", "Price", "Status", "Timestamp"])
            
            orders_list = []
            for order in orders_data:
                # Use filled price if available, otherwise limit/market price
                price = order.get('filled_avg_price') or order.get('limit_price') or order.get('stop_price') or 0
                price_str = f"${float(price):.2f}" if price else "Market"
                
                # Use filled quantity if available, otherwise ordered quantity
                quantity = order.get('filled_qty') or order.get('qty') or 0
                
                # Clean up status
                status = str(order.get('status', '')).replace('OrderStatus.', '').title()
                
                # Use appropriate timestamp
                timestamp = order.get('filled_at') or order.get('submitted_at') or order.get('created_at') or ""
                
                orders_list.append({
                    "Symbol": order.get("symbol", ""),
                    "Side": order.get("side", "").upper(),
                    "Quantity": float(quantity),
                    "Price": price_str,
                    "Status": status,
                    "Timestamp": str(timestamp)[:19] if timestamp else ""  # Trim to readable format
                })
            
            return pd.DataFrame(orders_list)
        except Exception as e:
            print(f"Error getting orders for {self.name}: {e}")
            return pd.DataFrame(columns=["Symbol", "Side", "Quantity", "Price", "Status", "Timestamp"])

    def get_portfolio_chart(self):
        """Get portfolio chart for this trader"""
        return create_trader_portfolio_chart(self.name)

    def reload(self):
        """Refresh trader data"""
        if hasattr(self.trader, 'reload'):
            self.trader.reload()

# Create trader instances dynamically using trading_floor.py approach
traders = create_traders()  # Dynamic: Use create_traders() from trading_floor.py
trader_views = [TraderView(trader) for trader in traders]

def get_trading_status():
    """Get current trading bot status - matches trading_floor.py functionality"""
    # Import trading_floor configuration
    from trading_floor import RUN_EVERY_N_MINUTES, USE_MIXED_MODELS, DEFAULT_MODEL_PROVIDER
    
    status_text = f"""
    ## 🤖 Trading Bot Status
    
    **Status:** {'🟢 Running' if trading_status['running'] else '🔴 Stopped'}
    **Last Cycle:** {trading_status['last_cycle']}
    **Cycles Completed:** {trading_status['cycles_completed']}
    
    **Configuration:**
    - **Run Interval:** {RUN_EVERY_N_MINUTES} minutes
    - **Mixed Models:** {USE_MIXED_MODELS}
    - **Default Provider:** {DEFAULT_MODEL_PROVIDER}
    - **Active Traders:** {len(names)} ({', '.join(names)})
    - **Models:** {', '.join(short_model_names)}
    
    **Recent Errors:** {len(trading_status['errors'])} errors
    """
    
    if trading_status['errors']:
        status_text += "\n**Latest Errors:**\n"
        for error in trading_status['errors'][-3:]:  # Show last 3 errors
            status_text += f"- {error}\n"
    
    return status_text

def refresh_trader_data():
    """Refresh all trader data"""
    for trader in traders:
        trader.reload()
    return "✅ Data refreshed successfully!"

def get_logs():
    """Get recent trading logs"""
    try:
        # Get logs for all traders
        all_logs = []
        for trader_name in ["warren", "ray", "cathie"]:
            try:
                trader_logs = list(read_log(trader_name, last_n=20))
                for log_entry in trader_logs:
                    if len(log_entry) >= 3:
                        timestamp, log_type, message = log_entry
                        all_logs.append({
                            'trader': trader_name.title(),
                            'timestamp': timestamp,
                            'type': log_type,
                            'message': message
                        })
            except Exception as trader_error:
                continue
        
        if all_logs:
            # Sort by timestamp (most recent first)
            all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
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

# =============================================================================
# NEW: Portfolio Tracking and Enhanced UI Functions
# =============================================================================

def log_portfolio_snapshots():
    """Collect and log portfolio snapshots for all traders"""
    try:
        snapshots_logged = 0
        # Use dynamic trader names from trading_floor.py
        for trader_name in names:  # Dynamic: Use names from trading_floor.py
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
                    trader=trader_name.lower(),  # Store as lowercase for consistency
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

def create_trader_portfolio_chart(trader_name, days=30):
    """Create portfolio chart for a specific trader"""
    try:
        # Get history for specific trader
        history = read_portfolio_history(trader_name.lower(), days=days)
        
        if not history:
            # Create empty chart with message
            fig = px.line(title=f"📊 {trader_name} Portfolio Value")
            fig.add_annotation(
                text=f"No portfolio history for {trader_name} yet.<br>Click 'Log Portfolio Snapshots' to start collecting data.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color="gray")
            )
            fig.update_layout(height=300)
            return fig
        
        # Convert to DataFrame
        df = pd.DataFrame(history)
        df['Date'] = pd.to_datetime(df['timestamp'])
        
        # Create line chart
        fig = px.line(
            df, 
            x='Date', 
            y='portfolio_value',
            title=f'📊 {trader_name} Portfolio Value Over Time',
            hover_data=['cash', 'positions_count', 'total_pl']
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            height=300
        )
        
        return fig
    except Exception as e:
        fig = px.line(title=f"Chart Error: {str(e)}")
        return fig

def get_portfolio_chart_data():
    """Get portfolio data for Gradio chart component"""
    return create_portfolio_chart()

def refresh_portfolio_data():
    """Refresh portfolio snapshots and return updated chart"""
    log_result = log_portfolio_snapshots()
    chart = create_portfolio_chart()
    orders = get_recent_orders_data()
    return chart, orders, log_result

def start_portfolio_tracking():
    """Start periodic portfolio snapshot logging in background"""
    def periodic_snapshot():
        while True:
            try:
                time.sleep(300)  # Log every 5 minutes
                if trading_status["running"]:
                    log_portfolio_snapshots()
                    print(f"📊 Portfolio snapshot logged at {datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"Portfolio tracking error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    # Start portfolio tracking in background thread
    portfolio_thread = threading.Thread(target=periodic_snapshot, daemon=True)
    portfolio_thread.start()
    print("📊 Periodic portfolio tracking started (every 5 minutes)")

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

# Create Gradio interface
with gr.Blocks(css=enhanced_css, js=js, title="AI Trading Bot Dashboard") as demo:
    gr.HTML("<h1 style='text-align: center; color: #2E8B57;'>🤖 AI Trading Bot - Enhanced Dashboard</h1>")
    
    # Trading Bot Status Section
    with gr.Row():
        with gr.Column():
            status_display = gr.Markdown(get_trading_status())
            refresh_status_btn = gr.Button("🔄 Refresh Status", variant="secondary")
            refresh_status_btn.click(fn=get_trading_status, outputs=status_display)
    
    # Main Tabs Section
    with gr.Tabs():
        # Individual trader tabs
        for i, trader_view in enumerate(trader_views):
            with gr.TabItem(f"{trader_view.name} ({trader_view.model_name})"):
                gr.HTML(trader_view.get_title())
                
                # Portfolio Chart
                with gr.Row():
                    portfolio_chart = gr.Plot(
                        value=trader_view.get_portfolio_chart(),
                        elem_classes=["portfolio-chart"]
                    )
                
                with gr.Row():
                    with gr.Column(scale=1):
                        account_info = gr.Markdown(trader_view.get_account_info())
                    with gr.Column(scale=2):
                        positions_df = gr.Dataframe(
                            value=trader_view.get_positions_df(),
                            headers=["Symbol", "Quantity", "Market Value", "Unrealized P&L"]
                        )
                
                # Recent Orders Table
                with gr.Row():
                    orders_df = gr.Dataframe(
                        value=trader_view.get_recent_orders_df(),
                        headers=["Symbol", "Side", "Quantity", "Price", "Status", "Timestamp"],
                        label=f"{trader_view.name}'s Recent Orders"
                    )
                
                refresh_btn = gr.Button(f"🔄 Refresh {trader_view.name}'s Data", variant="primary")
                refresh_btn.click(
                    fn=lambda tv=trader_view: (
                        tv.reload(), 
                        tv.get_account_info(), 
                        tv.get_positions_df(),
                        tv.get_recent_orders_df(),
                        tv.get_portfolio_chart()
                    )[1:],
                    outputs=[account_info, positions_df, orders_df, portfolio_chart]
                )
        
        # Enhanced Logs Tab
        with gr.TabItem("📋 Trading Logs"):
            gr.HTML("<h3 style='color: #2E8B57;'>Recent Trading Activity</h3>")
            logs_display = gr.Markdown(get_logs())
            refresh_logs_btn = gr.Button("🔄 Refresh Logs", variant="secondary")
            refresh_logs_btn.click(fn=get_logs, outputs=logs_display)
    
    # Auto-refresh every 30 seconds - removed due to Gradio version compatibility
    # Users can manually refresh using the refresh button

# Start trading bot and portfolio tracking when module loads
start_trading_bot()
start_portfolio_tracking()

if __name__ == "__main__":
    # Get port from environment (Railway sets this, otherwise try different ports)
    port = int(os.environ.get("PORT", 7861))  # Changed default to 7861
    
    print(f"🌐 Starting Gradio dashboard on port {port}")
    print(f"🤖 Trading bot running in background")
    
    # Launch Gradio with public access for Railway
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
        inbrowser=False  # Don't auto-open browser
    )
