from trading_agents.traders import Trader
from typing import List
import asyncio
from trading_agents.tracers import LogTracer
from core.alpaca_client import AlpacaClient
from dotenv import load_dotenv
import os

load_dotenv(override=True)

# Initialize default Alpaca client for market status (uses Warren's credentials as default)
alpaca_client = AlpacaClient(paper_trading=True, trader_name="Warren")

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)

# Trader personalities and names
names = ["Warren", "Ray", "Cathie"]
lastnames = ["Patience", "Systematic", "Crypto"]

# Simplified model selection: OpenAI and Anthropic only
DEFAULT_MODEL_PROVIDER = os.getenv("DEFAULT_MODEL_PROVIDER", "openai").lower()
USE_MIXED_MODELS = os.getenv("USE_MIXED_MODELS", "false").strip().lower() == "true"

if USE_MIXED_MODELS:
    # Mix of OpenAI and Anthropic models for diversity
    model_names = [
        "gpt-4o-mini",
        "gpt-4o",
        "claude-3-5-sonnet-20241022"
    ]
    short_model_names = ["GPT 4o Mini", "GPT 4o", "Claude 3.5 Sonnet"]
else:
    # Single provider mode
    if DEFAULT_MODEL_PROVIDER == "anthropic":
        model_names = ["claude-3-5-haiku-20241022"] * 3
        short_model_names = ["Claude 3.5 Haiku"] * 3
    else:
        model_names = ["gpt-4o-mini"] * 3
        short_model_names = ["GPT 4o Mini"] * 3


def create_traders() -> List[Trader]:
    traders = []
    for name, lastname, model_name in zip(names, lastnames, model_names):
        traders.append(Trader(name, lastname, model_name))
    return traders


async def run_trading_cycle():
    """Run a single trading cycle for all traders"""
    # Initialize simple logging (removed educational framework)
    logger = LogTracer()
    traders = create_traders()
    
    print(f"\n🤖 Running {len(traders)} traders with models: {short_model_names}")
    
    # Execute all traders concurrently
    results = await asyncio.gather(*[trader.run() for trader in traders], return_exceptions=True)
    
    # Log any errors
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ Trader {names[i]} failed: {result}")
        else:
            print(f"✅ Trader {names[i]} completed successfully")

async def run_every_n_minutes():
    """Main trading loop"""
    print(f"🚀 Starting Production Trading System")
    print(f"   Mixed Models: {USE_MIXED_MODELS}")
    print(f"   Default Provider: {DEFAULT_MODEL_PROVIDER}")
    print(f"   Run Interval: {RUN_EVERY_N_MINUTES} minutes")
    
    while True:
        try:
            # Check market status
            market_status = alpaca_client.get_market_status()
            market_open = market_status.get("is_open", False)
            
            if RUN_EVEN_WHEN_MARKET_IS_CLOSED or market_open:
                print(f"\n📊 Market Status: {'OPEN' if market_open else 'CLOSED'}")
                await run_trading_cycle()
                print(f"✅ Trading cycle completed")
            else:
                print(f"\n⏸️  Market closed - skipping (next check in {RUN_EVERY_N_MINUTES} minutes)")
                
        except Exception as e:
            print(f"❌ Trading cycle error: {e}")
            
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_every_n_minutes())
    except KeyboardInterrupt:
        print("\n🛑 Trading system stopped by user")
    except Exception as e:
        print(f"💥 System error: {e}")
