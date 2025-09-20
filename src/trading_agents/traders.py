from contextlib import AsyncExitStack
from accounts_client import read_accounts_resource, read_strategy_resource
from trading_agents.tracers import make_trace_id
from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json
from agents.mcp import MCPServerStdio
from trading_agents.templates import (
    researcher_instructions,
    trader_instructions,
    trading_session_message,
)
from config.mcp_params import trader_mcp_server_params, researcher_mcp_server_params

load_dotenv(override=True)

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
grok_api_key = os.getenv("GROK_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
GROK_BASE_URL = "https://api.x.ai/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MAX_TURNS = 30

openrouter_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=openrouter_api_key)
deepseek_client = AsyncOpenAI(base_url=DEEPSEEK_BASE_URL, api_key=deepseek_api_key)
grok_client = AsyncOpenAI(base_url=GROK_BASE_URL, api_key=grok_api_key)
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)


def get_model(model_name: str):
    if "/" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=openrouter_client)
    elif "deepseek" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=deepseek_client)
    elif "grok" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=grok_client)
    elif "gemini" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=gemini_client)
    else:
        return model_name


async def get_researcher(mcp_servers, model_name) -> Agent:
    researcher = Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=get_model(model_name),
        mcp_servers=mcp_servers,
    )
    return researcher


async def get_researcher_tool(mcp_servers, model_name) -> Tool:
    researcher = await get_researcher(mcp_servers, model_name)
    return researcher.as_tool(tool_name="Researcher", tool_description="Research tool for market analysis and opportunity identification")


class Trader:
    def __init__(self, name: str, lastname="Trader", model_name="gpt-4o-mini"):
        self.name = name
        self.lastname = lastname
        self.agent = None
        self.model_name = model_name
        self._strategy = None  # Cache strategy as identity

    async def create_agent(self, trader_mcp_servers, researcher_mcp_servers) -> Agent:
        # Load strategy as identity (once)
        if not self._strategy:
            self._strategy = await self._load_strategy()
            
        tool = await get_researcher_tool(researcher_mcp_servers, self.model_name)
        self.agent = Agent(
            name=self.name,
            instructions=trader_instructions(self.name, self._strategy),
            model=get_model(self.model_name),
            tools=[tool],
            mcp_servers=trader_mcp_servers,
        )
        return self.agent

    async def _load_strategy(self):
        """Load strategy as agent identity"""
        try:
            return await read_strategy_resource(self.name)
        except Exception as e:
            print(f"Strategy load failed for {self.name}: {e}")
            return f"Default investment strategy for {self.name}"

    async def get_account_report(self) -> str:
        # Use the portfolio summary tool which returns structured JSON data
        from accounts_client import call_accounts_tool
        try:
            result = await call_accounts_tool('get_portfolio_summary', {'name': self.name})
            # Extract the JSON content from the MCP result
            if hasattr(result, 'content') and result.content:
                return result.content[0].text
            elif hasattr(result, 'structuredContent'):
                return json.dumps(result.structuredContent.get('result', {}))
            else:
                return json.dumps({})
        except Exception as e:
            print(f"Warning: Could not get portfolio summary for {self.name}: {e}")
            # Fallback to empty portfolio data
            return json.dumps({
                "account_name": self.name,
                "cash_balance": 1000.0,
                "portfolio_value": 1000.0,
                "holdings": {}
            })

    async def get_trading_guidance(self) -> str:
        # Get trading guidance with risk limits and available funds
        from accounts_client import call_accounts_tool
        try:
            result = await call_accounts_tool('get_trading_guidance', {'name': self.name})
            if hasattr(result, 'content') and result.content:
                return result.content[0].text
            else:
                return "❌ Could not retrieve trading guidance"
        except Exception as e:
            print(f"Warning: Could not get trading guidance for {self.name}: {e}")
            return f"❌ Trading guidance unavailable: {e}"

    async def run_agent(self, trader_mcp_servers, researcher_mcp_servers):
        """Unified agent execution - strategy as identity, memory-driven sessions"""
        try:
            self.agent = await self.create_agent(trader_mcp_servers, researcher_mcp_servers)
            
            # Get current account status for session
            account = await self.get_account_report()
            
            # Build unified message
            message = self._build_unified_message(account)
            
            # Execute unified trading session
            await Runner.run(self.agent, message, max_turns=MAX_TURNS)
            
        except Exception as e:
            print(f"Agent {self.name} execution failed: {e}")
            raise

    def _build_unified_message(self, account: str):
        """Build unified trading message with strategy as identity"""
        # Session uses memory and account status
        session_message = trading_session_message(self.name, account)
        
        # Mandatory guidance reminder
        guidance_reminder = """
MANDATORY FIRST ACTION: Call get_trading_guidance before any trading decisions.
This shows your funds, limits, current positions, and portfolio status.
"""
        
        return f"{guidance_reminder}\n\n{session_message}"

    async def run_with_mcp_servers(self):
        async with AsyncExitStack() as stack:
            trader_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in trader_mcp_server_params()  # Call function instead of using as variable
            ]
            async with AsyncExitStack() as stack:
                researcher_mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params(self.name)
                ]
                await self.run_agent(trader_mcp_servers, researcher_mcp_servers)

    async def run_with_trace(self):
        trace_name = f"{self.name}-trading"  # Unified approach - no more rebalancing split
        trace_id = make_trace_id(f"{self.name.lower()}")
        with trace(trace_name, trace_id=trace_id):
            await self.run_with_mcp_servers()

    async def run(self):
        """Run unified trading session"""
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
        # No more do_trade toggle - unified approach
