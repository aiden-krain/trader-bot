import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Environment configurations for search services
brave_env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}
serper_env = {"SERPER_API_KEY": os.getenv("SERPER_API_KEY")}

# Production MCP servers using Alpaca for real trading
def trader_mcp_server_params():
    """
    Enhanced production MCP server parameters for traders.
    Uses Alpaca for real market data and trading, plus dual search for research.
    """
    
    servers = [
        # Core trading functionality
        {"command": "uv", "args": ["run", "production_accounts_server.py"]},
        {"command": "uv", "args": ["run", "alpaca_server.py"]},
        {"command": "uv", "args": ["run", "push_server.py"]},
    ]
    
    # Add dual search capabilities for enhanced market research
    # Both Serper (Google) and Brave Search for comprehensive coverage
    if os.getenv("SERPER_API_KEY"):
        servers.append({
            "command": "uvx", 
            "args": ["mcp-server-serper"], 
            "env": serper_env
        })
    
    if os.getenv("BRAVE_API_KEY"):
        servers.append({
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": brave_env,
        })
    
    # Add memory for persistent agent learning
    servers.append({"command": "uvx", "args": ["mcp-server-memory"]})
    
    return servers

# Enhanced researcher MCP servers with dual search capabilities

def researcher_mcp_server_params(name: str):
    """
    Enhanced researcher MCP parameters with dual search for comprehensive market research.
    Combines Serper (Google), Brave Search, web fetch, and persistent memory.
    """
    servers = [
        # Web content fetching
        {"command": "uvx", "args": ["mcp-server-fetch"]},
        
        # Persistent memory for research continuity
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:./memory/{name}.db"},
        },
    ]
    
    # Dual search setup for comprehensive coverage
    if os.getenv("SERPER_API_KEY"):
        servers.append({
            "command": "uvx", 
            "args": ["mcp-server-serper"], 
            "env": serper_env
        })
    
    if os.getenv("BRAVE_API_KEY"):
        servers.append({
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": brave_env,
        })
    
    return servers

# Backward compatibility function for existing code
def get_trader_mcp_params():
    """Backward compatibility wrapper"""
    return trader_mcp_server_params()
