import gradio as gr
from utils.util import css, js, Color
import pandas as pd
from trading_floor import names, lastnames, short_model_names
import plotly.express as px
from core.alpaca_client import AlpacaClient
from utils.database import read_log
import json
from datetime import datetime

mapper = {
    "trace": Color.WHITE,
    "agent": Color.CYAN,
    "function": Color.GREEN,
    "generation": Color.YELLOW,
    "response": Color.MAGENTA,
    "account": Color.RED,
}


class Trader:
    def __init__(self, name: str, lastname: str, model_name: str):
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self.account_data = None
        self.positions = []
        # Initialize Alpaca client for this trader
        self.alpaca_client = AlpacaClient(paper_trading=True, trader_name=name)
        self.reload()

    def reload(self):
        """Refresh account data from Alpaca API"""
        try:
            self.account_data = self.alpaca_client.get_account_info()
            self.positions = self.alpaca_client.get_positions()
        except Exception as e:
            print(f"Error loading account data for {self.name}: {e}")
            self.account_data = {"portfolio_value": 0, "cash": 0}
            self.positions = []

    def get_title(self) -> str:
        return f"<div style='text-align: center;font-size:34px;'>{self.name}<span style='color:#ccc;font-size:24px;'> ({self.model_name}) - {self.lastname}</span></div>"

    def get_strategy(self) -> str:
        return "Alpaca Paper Trading - Direct API Integration"

    def get_portfolio_value_df(self) -> pd.DataFrame:
        """Create a simple time series with current portfolio value"""
        # For now, create a simple chart with current value
        # In a full implementation, you'd store historical data
        current_time = datetime.now()
        portfolio_value = float(self.account_data.get('portfolio_value', 0))
        
        # Create a simple chart with some recent data points
        data = [
            [current_time.strftime("%Y-%m-%d %H:%M:%S"), portfolio_value]
        ]
        
        df = pd.DataFrame(data, columns=["datetime", "value"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    def get_portfolio_value_chart(self):
        df = self.get_portfolio_value_df()
        fig = px.line(df, x="datetime", y="value")
        margin = dict(l=40, r=20, t=20, b=40)
        fig.update_layout(
            height=300,
            margin=margin,
            xaxis_title=None,
            yaxis_title=None,
            paper_bgcolor="#bbb",
            plot_bgcolor="#dde",
        )
        fig.update_xaxes(tickformat="%m/%d", tickangle=45, tickfont=dict(size=8))
        fig.update_yaxes(tickfont=dict(size=8), tickformat=",.0f")
        return fig

    def get_holdings_df(self) -> pd.DataFrame:
        """Convert holdings to DataFrame for display"""
        if not self.positions:
            return pd.DataFrame(columns=["Symbol", "Quantity", "Market Value", "Unrealized P&L"])

        holdings_data = []
        for pos in self.positions:
            if pos['qty'] != 0:  # Only show non-zero positions
                holdings_data.append({
                    "Symbol": pos['symbol'],
                    "Quantity": pos['qty'],
                    "Market Value": f"${pos['market_value']:,.2f}",
                    "Unrealized P&L": f"${pos['unrealized_pl']:,.2f}"
                })
        
        if not holdings_data:
            return pd.DataFrame(columns=["Symbol", "Quantity", "Market Value", "Unrealized P&L"])
        
        return pd.DataFrame(holdings_data)

    def get_transactions_df(self) -> pd.DataFrame:
        """Convert recent orders to DataFrame for display"""
        try:
            # For now, return empty DataFrame since get_orders method needs to be added to AlpacaClient
            # TODO: Add get_orders method to AlpacaClient class
            return pd.DataFrame(columns=["Timestamp", "Symbol", "Side", "Quantity", "Avg Price"])
            
            # This code will be used once get_orders is implemented:
            # orders = self.alpaca_client.get_orders(status="filled", limit=10)
            # if not orders:
            #     return pd.DataFrame(columns=["Timestamp", "Symbol", "Side", "Quantity", "Avg Price"])

            # transactions_data = []
            # for order in orders:
            #     transactions_data.append({
            #         "Timestamp": order.get("filled_at", order.get("submitted_at", ""))[:19],  # Trim to date/time
            #         "Symbol": order["symbol"],
            #         "Side": order["side"].upper(),
            #         "Quantity": order.get("filled_qty", order["qty"]),
            #         "Avg Price": f"${order.get('avg_fill_price', 0):.2f}" if order.get('avg_fill_price') else "N/A"
            #     })
            
            return pd.DataFrame(transactions_data)
        except Exception as e:
            print(f"Error getting transactions: {e}")
            return pd.DataFrame(columns=["Timestamp", "Symbol", "Side", "Quantity", "Avg Price"])

    def get_portfolio_value(self) -> str:
        """Get portfolio value from Alpaca account data"""
        if not self.account_data:
            return "<div style='text-align: center;background-color:gray;'><span style='font-size:32px'>$0</span></div>"
        
        portfolio_value = float(self.account_data.get('portfolio_value', 0))
        equity = float(self.account_data.get('equity', 0))
        last_equity = float(self.account_data.get('last_equity', equity))
        
        # Calculate daily P&L
        daily_pnl = equity - last_equity
        color = "green" if daily_pnl >= 0 else "red"
        emoji = "⬆" if daily_pnl >= 0 else "⬇"
        
        return f"<div style='text-align: center;background-color:{color};padding:10px;'><span style='font-size:32px'>${portfolio_value:,.0f}</span><span style='font-size:24px'>&nbsp;&nbsp;&nbsp;{emoji}&nbsp;${daily_pnl:,.0f}</span></div>"

    def get_logs(self, previous=None) -> str:
        logs = read_log(self.name, last_n=13)
        response = ""
        for log in logs:
            timestamp, type, message = log
            color = mapper.get(type, Color.WHITE).value
            response += f"<span style='color:{color}'>{timestamp} : [{type}] {message}</span><br/>"
        response = f"<div style='height:250px; overflow-y:auto;'>{response}</div>"
        if response != previous:
            return response
        return gr.update()


class TraderView:
    def __init__(self, trader: Trader):
        self.trader = trader
        self.portfolio_value = None
        self.chart = None
        self.holdings_table = None
        self.transactions_table = None

    def make_ui(self):
        with gr.Column():
            gr.HTML(self.trader.get_title())
            with gr.Row():
                self.portfolio_value = gr.HTML(self.trader.get_portfolio_value)
            with gr.Row():
                self.chart = gr.Plot(
                    self.trader.get_portfolio_value_chart, container=True, show_label=False
                )
            with gr.Row(variant="panel"):
                self.log = gr.HTML(self.trader.get_logs)
            with gr.Row():
                self.holdings_table = gr.Dataframe(
                    value=self.trader.get_holdings_df,
                    label="Current Positions (Live from Alpaca)",
                    headers=["Symbol", "Quantity", "Market Value", "Unrealized P&L"],
                    row_count=(5, "dynamic"),
                    col_count=4,
                    max_height=300,
                    elem_classes=["dataframe-fix-small"],
                )
            with gr.Row():
                self.transactions_table = gr.Dataframe(
                    value=self.trader.get_transactions_df,
                    label="Recent Orders (Live from Alpaca)",
                    headers=["Timestamp", "Symbol", "Side", "Quantity", "Avg Price"],
                    row_count=(5, "dynamic"),
                    col_count=5,
                    max_height=300,
                    elem_classes=["dataframe-fix"],
                )

        timer = gr.Timer(value=120)
        timer.tick(
            fn=self.refresh,
            inputs=[],
            outputs=[
                self.portfolio_value,
                self.chart,
                self.holdings_table,
                self.transactions_table,
            ],
            show_progress="hidden",
            queue=False,
        )
        log_timer = gr.Timer(value=0.5)
        log_timer.tick(
            fn=self.trader.get_logs,
            inputs=[self.log],
            outputs=[self.log],
            show_progress="hidden",
            queue=False,
        )

    def refresh(self):
        self.trader.reload()
        return (
            self.trader.get_portfolio_value(),
            self.trader.get_portfolio_value_chart(),
            self.trader.get_holdings_df(),
            self.trader.get_transactions_df(),
        )


# Main UI construction
def create_ui():
    """Create the main Gradio UI for the trading simulation"""

    traders = [
        Trader(trader_name, lastname, model_name)
        for trader_name, lastname, model_name in zip(names, lastnames, short_model_names)
    ]
    trader_views = [TraderView(trader) for trader in traders]

    with gr.Blocks(
        title="Traders", css=css, js=js, theme=gr.themes.Default(primary_hue="sky"), fill_width=True
    ) as ui:
        with gr.Row():
            for trader_view in trader_views:
                trader_view.make_ui()

    return ui


if __name__ == "__main__":
    ui = create_ui()
    ui.launch(inbrowser=True)
