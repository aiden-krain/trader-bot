"""
Combined application that runs both the trading bot and Gradio dashboard
This allows Railway to serve both the web interface and run the trading bot
"""
import asyncio
import threading
import time
from trading_floor import run_every_n_minutes
import gradio as gr
from utils.util import css, js, Color
import pandas as pd
from trading_floor import names, lastnames, short_model_names
import plotly.express as px
from utils.database import read_log
from trading_agents.traders import Trader
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
    """Start the trading bot in a background thread"""
    global trading_status
    
    async def run_bot():
        trading_status["running"] = True
        trading_status["last_cycle"] = f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            await run_every_n_minutes()
        except Exception as e:
            trading_status["errors"].append(f"{datetime.now()}: {str(e)}")
            trading_status["running"] = False
    
    # Run the trading bot in a separate thread
    def run_in_thread():
        asyncio.run(run_bot())
    
    trading_thread = threading.Thread(target=run_in_thread, daemon=True)
    trading_thread.start()
    print("🚀 Trading bot started in background thread")

# Start trading bot when module loads
start_trading_bot()

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

    def reload(self):
        """Refresh trader data"""
        if hasattr(self.trader, 'reload'):
            self.trader.reload()

# Create trader instances and their UI wrappers
traders = [Trader(name, lastname, model) for name, lastname, model in zip(names, lastnames, short_model_names)]
trader_views = [TraderView(trader) for trader in traders]

def get_trading_status():
    """Get current trading bot status"""
    status_text = f"""
    ## 🤖 Trading Bot Status
    
    **Status:** {'🟢 Running' if trading_status['running'] else '🔴 Stopped'}
    **Last Cycle:** {trading_status['last_cycle']}
    **Cycles Completed:** {trading_status['cycles_completed']}
    
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

# Create Gradio interface
with gr.Blocks(css=css, js=js, title="AI Trading Bot Dashboard") as demo:
    gr.HTML("<h1 style='text-align: center; color: #2E8B57;'>🤖 AI Trading Bot - Live Dashboard</h1>")
    
    # Trading Bot Status Section
    with gr.Row():
        with gr.Column():
            status_display = gr.Markdown(get_trading_status())
            refresh_status_btn = gr.Button("🔄 Refresh Status", variant="secondary")
            refresh_status_btn.click(fn=get_trading_status, outputs=status_display)
    
    # Traders Section
    with gr.Tabs():
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
        
        # Logs Tab
        with gr.TabItem("📋 Trading Logs"):
            logs_display = gr.Markdown(get_logs())
            refresh_logs_btn = gr.Button("🔄 Refresh Logs", variant="secondary")
            refresh_logs_btn.click(fn=get_logs, outputs=logs_display)
    
    # Auto-refresh every 30 seconds - removed due to Gradio version compatibility
    # Users can manually refresh using the refresh button

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
