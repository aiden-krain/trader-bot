import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Environment configurations for search services
brave_env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}

# Production MCP servers using Alpaca for real trading
def trader_mcp_server_params():
    """
    Decomposed MCP server parameters for traders.
    Uses focused server architecture: trading, account, market data, and notifications.
    """
    
    # Get the src directory path
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    servers = [
        # Decomposed server architecture - focused responsibilities  
        {"command": "uv", "args": ["run", os.path.join(src_dir, "servers/trading_server.py")], "env": {"PYTHONPATH": src_dir}, "cwd": src_dir},
        {"command": "uv", "args": ["run", os.path.join(src_dir, "servers/account_server.py")], "env": {"PYTHONPATH": src_dir}, "cwd": src_dir},
        {"command": "uv", "args": ["run", os.path.join(src_dir, "servers/market_data_server.py")], "env": {"PYTHONPATH": src_dir}, "cwd": src_dir},
        {"command": "uv", "args": ["run", os.path.join(src_dir, "servers/push_server.py")], "env": {"PYTHONPATH": src_dir}, "cwd": src_dir},
    ]
    
    if os.getenv("BRAVE_API_KEY"):
        servers.append({
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": brave_env,
        })
    
    return servers

# Enhanced researcher MCP servers with dual search capabilities

def researcher_mcp_server_params(name: str):
    """
    Enhanced researcher MCP parameters with dual search for comprehensive market research.
    Combines Serper (Google), Brave Search, web fetch, and persistent memory.
    """
    # Get the src directory path for absolute database paths
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    memory_db_path = os.path.join(src_dir, "memory", f"{name}.db")
    
    servers = [
        # Web content fetching
        {"command": "uvx", "args": ["mcp-server-fetch"], "cwd": src_dir},
        
        # Persistent memory for research continuity
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:{memory_db_path}"},
            "cwd": src_dir
        },
    ]
    
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
