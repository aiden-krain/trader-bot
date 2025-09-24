#!/usr/bin/env python3
"""
Hugging Face Spaces entry point for AI Trading Bot.
Optimized for Hugging Face deployment with simplified MCP configuration.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main application
if __name__ == "__main__":
    from combined_app import trading_bot
    
    # Hugging Face Spaces uses port 7860 by default
    port = int(os.environ.get("PORT", 7860))
    
    print(f"🚀 Starting AI Trading Bot on Hugging Face Spaces (port {port})")
    
    # Launch with Hugging Face Spaces optimized settings
    trading_bot.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
        inbrowser=False,
        # Hugging Face Spaces specific settings
        enable_queue=True,
        max_threads=10
    )
