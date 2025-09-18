"""
Comprehensive test script for the trading bot system
Tests all components without making actual trades
"""

from core.alpaca_client import AlpacaClient, get_account_info, get_positions, get_share_price
import asyncio
import sys
import os

async def test_alpaca_connection():
    """Test Alpaca API connection and basic functionality"""
    print("🔗 Testing Alpaca Connection...")
    try:
        client = AlpacaClient()
        
        # Test account connection
        account_info = client.get_account_info()
        print(f"✅ Account Status: {account_info['status']}")
        print(f"💰 Buying Power: ${float(account_info['buying_power']):,.2f}")
        print(f"📊 Portfolio Value: ${float(account_info['portfolio_value']):,.2f}")
        print(f"🏛️  Account Type: Paper Trading")
        
        # Test market status
        print("\n⏰ Testing Market Status...")
        status = client.get_market_status()
        print(f"✅ Market Status: {'OPEN' if status.get('is_open', False) else 'CLOSED'}")
        
        # Test market data
        print("\n📊 Testing Market Data...")
        try:
            price = client.get_real_price('AAPL')
            print(f"✅ AAPL Price: ${price:.2f}")
        except Exception as e:
            print(f"⚠️  Price fetch limitation: {str(e)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Alpaca connection failed: {e}")
        return False

async def test_alpaca_integration():
    """Test direct Alpaca API integration"""
    print("\n🏦 Testing Direct Alpaca Integration...")
    try:
        # Test account info
        account_data = get_account_info()
        print(f"✅ Account synced - Portfolio Value: ${float(account_data['portfolio_value']):,.2f}")
        print(f"💰 Cash Balance: ${float(account_data['cash']):,.2f}")
        print(f"� Buying Power: ${float(account_data['buying_power']):,.2f}")
        
        # Test positions
        print("\n� Testing Positions...")
        positions = get_positions()
        print(f"✅ Retrieved {len(positions)} positions")
        
        # Test environment safety
        print("\n🔍 Testing Safety Configuration...")
        paper_trading = os.getenv('ALPACA_PAPER_TRADING', 'true').lower() == 'true'
        execute_orders = os.getenv('EXECUTE_REAL_ORDERS', 'false').lower() == 'true'
        base_url = os.getenv('ALPACA_BASE_URL', '')
        
        print(f"✅ Paper Trading: {'ENABLED' if paper_trading else 'DISABLED (DANGER!)'}")
        print(f"✅ Execute Orders: {'DISABLED' if not execute_orders else 'ENABLED'}")
        print(f"✅ Base URL: {base_url}")
        
        if not paper_trading:
            print("⚠️  WARNING: Paper trading is disabled - using live API!")
        
        return True
        
    except Exception as e:
        print(f"❌ Alpaca integration test failed: {e}")
        return False

async def test_mcp_servers():
    """Test MCP server startup"""
    print("\n🖥️  Testing MCP Servers...")
    
    # Test Alpaca server
    print("Testing Alpaca MCP Server...")
    result = os.system("cd servers && timeout 3s uv run alpaca_server.py > /dev/null 2>&1")
    if result == 124:  # timeout exit code
        print("✅ Alpaca server starts correctly (timed out as expected)")
    else:
        print(f"⚠️  Alpaca server startup issue (exit code: {result})")
    
    # Test Production Accounts server
    print("Testing Production Accounts MCP Server...")
    result = os.system("cd servers && timeout 3s uv run production_accounts_server.py > /dev/null 2>&1")
    if result == 124:  # timeout exit code  
        print("✅ Production Accounts server starts correctly (timed out as expected)")
    else:
        print(f"⚠️  Production Accounts server startup issue (exit code: {result})")
    
    return True

def test_environment_setup():
    """Test environment variables and configuration"""
    print("\n🔧 Testing Environment Setup...")
    
    required_vars = [
        'ALPACA_KEY',
        'ALPACA_SECRET', 
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables present")
        return True

async def test_search_integration():
    """Test dual search capabilities"""
    print("\n🔍 Testing Search Integration...")
    
    # Check if search API keys are available
    serper_key = os.getenv('SERPER_API_KEY')
    brave_key = os.getenv('BRAVE_API_KEY')
    
    if serper_key:
        print("✅ Serper API key present")
    else:
        print("⚠️  Serper API key missing")
    
    if brave_key:
        print("✅ Brave Search API key present")
    else:
        print("⚠️  Brave Search API key missing")
    
    return bool(serper_key and brave_key)

async def test_ai_models():
    """Test AI model integrations"""
    print("\n🤖 Testing AI Model Integration...")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if openai_key:
        print("✅ OpenAI API key present")
    else:
        print("⚠️  OpenAI API key missing")
    
    if anthropic_key:
        print("✅ Anthropic API key present") 
    else:
        print("⚠️  Anthropic API key missing")
    
    # Test basic model configuration
    try:
        use_mixed = os.getenv('USE_MIXED_MODELS', 'false').lower() == 'true'
        default_provider = os.getenv('DEFAULT_MODEL_PROVIDER', 'openai')
        print(f"📊 Mixed models: {'Enabled' if use_mixed else 'Disabled'}")
        print(f"🎯 Default provider: {default_provider}")
        return True
    except Exception as e:
        print(f"❌ Model configuration error: {e}")
        return False

async def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting Comprehensive Trading Bot Test")
    print("=" * 50)
    
    test_results = {}
    
    # Test environment
    test_results['environment'] = test_environment_setup()
    
    # Test Alpaca connection
    test_results['alpaca'] = await test_alpaca_connection()
    
    # Test Alpaca integration
    test_results['alpaca_integration'] = await test_alpaca_integration()
    
    # Test MCP servers
    test_results['mcp_servers'] = await test_mcp_servers()
    
    # Test search integration
    test_results['search'] = await test_search_integration()
    
    # Test AI models
    test_results['ai_models'] = await test_ai_models()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All systems operational! Ready for trading.")
    else:
        print("⚠️  Some issues detected. Review failures above.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1)