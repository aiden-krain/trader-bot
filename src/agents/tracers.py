"""
Simplified tracing system for production trading bot
"""

from utils.database import write_log
import secrets
import string

ALPHANUM = string.ascii_lowercase + string.digits 

def make_trace_id(tag: str) -> str:
    """Return a trace ID"""
    tag += "0"
    pad_len = 32 - len(tag)
    random_suffix = ''.join(secrets.choice(ALPHANUM) for _ in range(pad_len))
    return f"trace_{tag}{random_suffix}"

class LogTracer:
    """Simplified logging tracer"""
    
    def __init__(self):
        pass
    
    def log_to_trader(self, name: str, type: str, message: str):
        """Helper to log messages to a specific trader"""
        write_log(name, type, message)

def log_agent_message(trader_name: str, message_type: str, content: str):
    """Log agent messages directly"""
    write_log(trader_name, message_type, content)

def log_trading_action(trader_name: str, action: str, details: str):
    """Log trading actions"""
    write_log(trader_name, "trading", f"{action}: {details}")
