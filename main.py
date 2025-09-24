#!/usr/bin/env python3
"""
Main entry point for Railway deployment.
Imports and runs the combined trading bot application.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main application
if __name__ == "__main__":
    from combined_app import trading_bot
    
    # Get port from environment (Railway sets this automatically)
    port = int(os.environ.get("PORT", 8080))
    
    print(f"🚀 Starting AI Trading Bot on port {port}")
    
    # Launch the application
    trading_bot.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
        inbrowser=False
    )
