from utils.database import write_log
import secrets
import string
import logging

ALPHANUM = string.ascii_lowercase + string.digits 

def make_trace_id(tag: str) -> str:
    """
    Return a string of the form 'trace_<tag><random>',
    where the total length after 'trace_' is 32 chars.
    """
    tag += "0"
    pad_len = 32 - len(tag)
    random_suffix = ''.join(secrets.choice(ALPHANUM) for _ in range(pad_len))
    return f"trace_{tag}{random_suffix}"

class LogTracer:
    """Simplified logging tracer that maintains compatibility with existing code"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_name_from_trace_id(self, trace_id: str) -> str | None:
        """Extract trader name from trace ID"""
        if not trace_id or "_" not in trace_id:
            return None
        name = trace_id.split("_")[1]
        if '0' in name:
            return name.split("0")[0]
        return None

    def log_activity(self, trace_id: str, activity_type: str, message: str) -> None:
        """Log activity to database and console"""
        name = self.get_name_from_trace_id(trace_id)
        if name:
            write_log(name, activity_type, message)
            self.logger.info(f"[{name}] {activity_type}: {message}")

    def force_flush(self) -> None:
        """Compatibility method - no-op"""
        pass

    def shutdown(self) -> None:
        """Compatibility method - no-op"""
        pass
