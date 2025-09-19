"""
Production Accounts Client - MCP client for production trading accounts.
Provides clean interface to production accounts server with resource and tool access.
"""

import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from typing import Dict, Any, List

# MCP server parameters for production accounts
params = StdioServerParameters(
    command="uv", 
    args=["run", "servers/accounts_server.py"], 
    env=None
)

async def call_accounts_tool(tool_name: str, tool_args: Dict[str, Any]) -> Any:
    """
    Call a tool on the production accounts server.
    
    Args:
        tool_name: Name of the tool to call
        tool_args: Arguments to pass to the tool
    
    Returns:
        Tool execution result
    """
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            return result
            
async def get_account_info(name):
    """Get account information - tries resource first, then falls back to tool"""
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            
            # Try resource first (newer approach)
            try:
                result = await session.read_resource(f"accounts://accounts_server/{name}")
                return result.contents[0].text
            except Exception:
                # Fall back to tool (legacy approach)
                result = await session.call_tool("get_account_info", {"name": name})
                return result.content[0].text
                
        
async def get_strategy(name):
    """Get strategy - tries resource first, then falls back to tool"""
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            
            # Try resource first (newer approach)
            try:
                result = await session.read_resource(f"accounts://strategy/{name}")
                return result.contents[0].text
            except Exception:
                # Fall back to tool (legacy approach)
                result = await session.call_tool("get_strategy", {"name": name})
                return result.content[0].text
                

# Legacy functions for backward compatibility
async def read_accounts_resource(name):
    """Legacy function - use get_account_info instead"""
    return await get_account_info(name)

async def read_strategy_resource(name):
    """Legacy function - use get_strategy instead"""
    return await get_strategy(name)

async def debug_server_info():
    """Debug function to see what the server actually provides"""
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            
            # List all resources
            resources = await session.list_resources()
            print(f"All resources: {[(r.uri, r.name, r.description) for r in resources.resources]}")
            
            # List all tools
            tools = await session.list_tools()
            print(f"All tools: {[(t.name, t.description) for t in tools.tools]}")
            
            return {
                'resources': resources.resources,
                'tools': tools.tools
            }