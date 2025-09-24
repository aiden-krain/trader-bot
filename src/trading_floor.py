from trading_agents.traders import Trader
from typing import List
import asyncio
from trading_agents.tracers import LogTracer
from trading_core.alpaca_client import AlpacaClient
from dotenv import load_dotenv
import os
import json

load_dotenv(override=True)

# We'll check market status within the trading cycle using the traders' clients

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
        "gpt-4o-mini",
        "gpt-4o"
    ]
    short_model_names = ["GPT 4o Mini", "GPT 4o Mini", "GPT 4o"]
else:
    # Single provider mode
    if DEFAULT_MODEL_PROVIDER == "anthropic":
        model_names = ["claude-3-5-haiku-latest"] * 3
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
    
    # Check market status using the first trader's client
    market_status = traders[0].alpaca_client.get_market_status()
    market_open = market_status.get("is_open", False)
    
    # Display market status with timezone info
    status_display = "OPEN" if market_open else "CLOSED"
    current_time_et = market_status.get("current_time_et", "Unknown")
    market_open_time = market_status.get("market_open", "09:30:00")
    market_close_time = market_status.get("market_close", "16:00:00")
    
    print(f"\n📊 Market Status: {status_display}")
    print(f"   🕒 Eastern Time: {current_time_et} (Market: {market_open_time} - {market_close_time})")
    
    if market_status.get("reason"):
        print(f"   📅 {market_status['reason']}")
    
    # Decide whether to trade or not
    if not (RUN_EVEN_WHEN_MARKET_IS_CLOSED or market_open):
        print(f"⏸️  Market closed - skipping trading")
        return False  # Indicate no trading occurred
    
    print(f"\n🤖 Running {len(traders)} traders with models: {short_model_names}")
    
    # Execute all traders concurrently for better performance
    results = await asyncio.gather(*[trader.run() for trader in traders], return_exceptions=True)
    
    # Log any errors with detailed exception information
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ Trader {names[i]} failed with exception:")
            print(f"   Exception type: {type(result).__name__}")
            print(f"   Exception message: {str(result)}")
            # Print the full exception traceback for debugging
            import traceback
            print(f"   Full traceback:")
            traceback.print_exception(type(result), result, result.__traceback__)
        else:
            print(f"✅ Trader {names[i]} completed successfully")
    
    return True  # Indicate trading occurred

async def run_every_n_minutes():
    """Main trading loop"""
    print(f"🚀 Starting Production Trading System")
    print(f"   Mixed Models: {USE_MIXED_MODELS}")
    print(f"   Default Provider: {DEFAULT_MODEL_PROVIDER}")
    print(f"   Run Interval: {RUN_EVERY_N_MINUTES} minutes")
    
    while True:
        try:
            # Run trading cycle (includes market status check)
            trading_occurred = await run_trading_cycle()
            
            if trading_occurred:
                print(f"✅ Trading cycle completed")
            else:
                print(f"⏸️  Skipping trading (next check in {RUN_EVERY_N_MINUTES} minutes)")
                
        except Exception as e:
            print(f"❌ Trading cycle error: {e}")
            import traceback
            traceback.print_exception(type(e), e, e.__traceback__)
            
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_every_n_minutes())
    except KeyboardInterrupt:
        print("\n🛑 Trading system stopped by user")
    except Exception as e:
        print(f"💥 System error: {e}")
        import traceback
        traceback.print_exception(type(e), e, e.__traceback__)
