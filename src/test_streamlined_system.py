"""
Test streamlined trading system with complete reporting and best practices
"""
from trading_agents.templates import trading_session_message, trader_instructions

def test_streamlined_with_reporting():
    """Test that streamlined system includes complete reporting requirements"""
    
    print("Testing streamlined trading system...")
    
    # Test trader instructions are concise but complete
    strategy = "Value investing in dividend stocks with strong fundamentals"
    trader_template = trader_instructions("Warren", strategy)
    
    # Key elements should be present
    assert "TRADING PHILOSOPHY" in trader_template
    assert "don't force trades" in trader_template.lower()
    assert "get_current_orders" in trader_template
    assert "get_recent_trades" in trader_template
    assert "Quality over quantity" in trader_template
    assert "When uncertain → DON'T TRADE" in trader_template
    assert len(trader_template) < 2000  # Keep it concise
    print("✓ Trader instructions are concise and include best practices")
    
    # Test session message includes complete reporting
    account = "Account: $10K cash, 3 positions"
    session_template = trading_session_message("Warren", account)
    
    # Essential best practices
    assert "When in doubt, don't trade" in session_template
    assert "holding cash is a position" in session_template.lower()
    assert "get_current_orders" in session_template
    assert "get_recent_trades" in session_template
    assert "TRADING PRINCIPLES" in session_template
    assert "DECISION FRAMEWORK" in session_template
    print("✓ Session includes comprehensive trading best practices")
    
    # Verify complete push notification requirements are present
    assert "PUSH NOTIFICATION (Include ALL details)" in session_template
    assert "TRADES EXECUTED:" in session_template
    assert "CURRENT ACCOUNT OVERVIEW:" in session_template
    assert "Cash Balance:" in session_template
    assert "Portfolio Value:" in session_template
    assert "Active Positions:" in session_template
    assert "Pending Orders:" in session_template
    assert "Top Holdings:" in session_template
    assert "MARKET OUTLOOK:" in session_template
    print("✓ Complete push notification requirements included")
    
    # Verify order management workflow
    assert "get_current_orders" in session_template
    assert "get_recent_trades" in session_template
    assert "Review:" in session_template
    print("✓ Order management workflow included")
    
    # Verify decision framework
    assert "Does this trade fit my strategy?" in session_template
    assert "Do I have strong conviction?" in session_template
    assert "If unsure → DON'T TRADE" in session_template
    print("✓ Decision framework with 'don't trade' principle included")
    
    # Check length is reasonable
    assert len(session_template) < 2000  # Keep it focused
    assert len(trader_template) < 1600   # Keep it concise
    print(f"✓ Templates are appropriately sized (Trader: {len(trader_template)}, Session: {len(session_template)})")
    
    print("\n✅ All streamlined trading system tests passed!")
    print("📈 Key features:")
    print("   - Order context: Check current orders and recent trades")
    print("   - Best practices: Quality over quantity, don't force trades")
    print("   - Complete reporting: Detailed push notifications")
    print("   - Concise prompts: Under 2000 chars for better AI processing")
    print("🛡️ Core principle: When uncertain → DON'T TRADE")

def test_template_content_quality():
    """Test specific trading wisdom is embedded"""
    
    print("\nTesting trading wisdom integration...")
    
    strategy = "Test strategy"
    trader = trader_instructions("TestTrader", strategy)
    session = trading_session_message("TestTrader", "Test account")
    
    # Core trading principles
    wisdom_elements = [
        "Quality over quantity",
        "Patience is profitable", 
        "Risk management is priority",
        "Cash is a position",
        "don't force trades",
        "When uncertain → DON'T TRADE",
        "Position size = conviction",
        "Never trade without clear rationale"
    ]
    
    combined_text = trader + session
    found_elements = []
    
    for element in wisdom_elements:
        if element.lower() in combined_text.lower():
            found_elements.append(element)
    
    assert len(found_elements) >= 6, f"Only found {len(found_elements)} wisdom elements: {found_elements}"
    print(f"✓ Found {len(found_elements)}/{len(wisdom_elements)} trading wisdom elements")
    
    # Order management integration
    order_elements = [
        "get_current_orders",
        "get_recent_trades", 
        "pending trades",
        "learn from history"
    ]
    
    order_found = [elem for elem in order_elements if elem.lower() in combined_text.lower()]
    assert len(order_found) >= 3, f"Missing order management elements: {order_found}"
    print(f"✓ Order management integration complete")
    
    print("✅ Trading wisdom integration validated!")

if __name__ == "__main__":
    try:
        test_streamlined_with_reporting()
        test_template_content_quality()
        print("\n🎉 Streamlined trading system validation completed successfully!")
        print("📊 System ready with enhanced order context and trading best practices")
    except Exception as e:
        print(f"\n❌ Template validation failed: {e}")
        raise