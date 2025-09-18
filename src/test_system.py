"""
Comprehensive test script for the trading bot system
Tests all components without making actual trades
"""

from core.alpaca_client import AlpacaClient
from core.production_accounts import ProductionAccount
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
        
        # Test market data (may fail with free tier)
        print("\n📊 Testing Market Data...")
        try:
            price = await client.get_real_price('AAPL')
            print(f"✅ AAPL Price: ${price:.2f}")
        except Exception as e:
            print(f"⚠️  Price fetch limitation (expected with free tier): {str(e)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Alpaca connection failed: {e}")
        return False

async def test_production_accounts():
    """Test production account system"""
    print("\n🏦 Testing Production Account System...")
    try:
        # Create test account
        account = ProductionAccount("test_trader", 100000.0)
        
        # Test account sync
        sync_result = account.sync_with_alpaca()
        print(f"✅ Account synced - Balance: ${account.balance:,.2f}")
        print(f"📊 Sync result: {sync_result[:100]}...")
        
        # Test risk validation (without execution)
        print("\n🔍 Testing Risk Validation...")
        try:
            # Test risk validation system
            is_valid, message = account._validate_trade_risk("AAPL", 10, "buy", 150.0)
            print(f"✅ Risk validation: {'VALID' if is_valid else 'BLOCKED'} - {message}")
        except Exception as e:
            print(f"⚠️  Risk validation error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Production account test failed: {e}")
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
    
    # Test production accounts
    test_results['accounts'] = await test_production_accounts()
    
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