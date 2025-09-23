"""
Optimized database utilities for AI Trading Bot.
Focused on activity logging and portfolio tracking for UI visualization.
Memory storage is handled by individual trader databases in src/memory/
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv(override=True)

# Database file for logging and portfolio tracking
DB = "trading_bot.db"

def _init_database():
    """Initialize database with optimized schema"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        
        # Activity logs table (optimized, backward compatible)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trader TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                type TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')
        
        # Portfolio snapshots for time-series tracking (NEW)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trader TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                portfolio_value REAL NOT NULL,
                cash REAL NOT NULL,
                positions_count INTEGER NOT NULL,
                total_pl REAL DEFAULT 0.0
            )
        ''')
        
        # Performance indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_trader_time ON logs(trader, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_trader_time ON portfolio_snapshots(trader, timestamp)')
        
        conn.commit()

# Initialize database on import
_init_database()

# =============================================================================
# LOGGING FUNCTIONS (Backward Compatible)
# =============================================================================

def write_log(name: str, type: str, message: str) -> None:
    """
    Write a log entry to the logs table.
    BACKWARD COMPATIBLE: Maintains exact same signature as before.
    
    Args:
        name (str): The trader name (warren, ray, cathie)
        type (str): The type of log entry (trading, risk, error, agent)
        message (str): The log message
    """
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs (trader, type, message)
                VALUES (?, ?, ?)
            ''', (name.lower(), type, message))
            conn.commit()
    except Exception as e:
        # Fallback to console if database fails
        print(f"Database log error: {e} - {name}: {message}")

def read_log(name: str, last_n: int = 10):
    """
    Read the most recent log entries for a trader.
    BACKWARD COMPATIBLE: Maintains exact same signature and return format.
    
    Args:
        name (str): The trader name to retrieve logs for
        last_n (int): Number of most recent entries to retrieve
        
    Returns:
        list: A list of tuples containing (datetime, type, message)
    """
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, type, message FROM logs 
                WHERE trader = ? 
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (name.lower(), last_n))
            
            return reversed(cursor.fetchall())
    except Exception as e:
        print(f"Database read error: {e}")
        return []

# =============================================================================
# ENHANCED LOGGING FUNCTIONS (NEW)
# =============================================================================

def read_recent_logs(trader: Optional[str] = None, log_types: Optional[List[str]] = None, 
                    limit: int = 20) -> List[Dict[str, Any]]:
    """
    Enhanced log reading with filtering and structured output for UI.
    
    Args:
        trader (str, optional): Filter by specific trader, None for all
        log_types (list, optional): Filter by log types (trading, risk, error, agent)
        limit (int): Maximum number of entries to return
        
    Returns:
        list: List of dictionaries with structured log data
    """
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            
            query = "SELECT trader, timestamp, type, message FROM logs"
            params = []
            conditions = []
            
            if trader:
                conditions.append("trader = ?")
                params.append(trader.lower())
            
            if log_types:
                placeholders = ','.join(['?' for _ in log_types])
                conditions.append(f"type IN ({placeholders})")
                params.extend(log_types)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'trader': row[0].title(),
                    'timestamp': row[1],
                    'type': row[2],
                    'message': row[3]
                })
            
            return logs
    except Exception as e:
        print(f"Database read error: {e}")
        return []

# =============================================================================
# PORTFOLIO TRACKING FUNCTIONS (NEW)
# =============================================================================

def write_portfolio_snapshot(trader: str, portfolio_value: float, cash: float, 
                           positions_count: int, total_pl: float = 0.0) -> None:
    """
    Log portfolio snapshot for time-series tracking and UI graphs.
    
    Args:
        trader (str): The trader name
        portfolio_value (float): Total portfolio value
        cash (float): Available cash
        positions_count (int): Number of positions held
        total_pl (float): Total profit/loss
    """
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO portfolio_snapshots 
                (trader, portfolio_value, cash, positions_count, total_pl)
                VALUES (?, ?, ?, ?, ?)
            ''', (trader.lower(), portfolio_value, cash, positions_count, total_pl))
            conn.commit()
    except Exception as e:
        print(f"Portfolio snapshot error: {e}")

def read_portfolio_history(trader: str, days: int = 30) -> List[Dict[str, Any]]:
    """
    Get portfolio history for graphing and analysis.
    
    Args:
        trader (str): The trader name
        days (int): Number of days of history to retrieve
        
    Returns:
        list: List of portfolio snapshots with structured data
    """
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            
            # Calculate date threshold
            threshold_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT timestamp, portfolio_value, cash, positions_count, total_pl
                FROM portfolio_snapshots 
                WHERE trader = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            ''', (trader.lower(), threshold_date.isoformat()))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'timestamp': row[0],
                    'portfolio_value': row[1],
                    'cash': row[2],
                    'positions_count': row[3],
                    'total_pl': row[4],
                    'trader': trader.title()
                })
            
            return history
    except Exception as e:
        print(f"Portfolio history error: {e}")
        return []

def read_all_portfolio_history(days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get portfolio history for all traders for comparison graphs.
    
    Args:
        days (int): Number of days of history to retrieve
        
    Returns:
        dict: Dictionary with trader names as keys and history lists as values
    """
    try:
        traders = ['warren', 'ray', 'cathie']
        all_history = {}
        
        for trader in traders:
            all_history[trader] = read_portfolio_history(trader, days)
        
        return all_history
    except Exception as e:
        print(f"All portfolio history error: {e}")
        return {}

def get_latest_portfolio_values() -> Dict[str, float]:
    """
    Get the most recent portfolio values for all traders.
    
    Returns:
        dict: Latest portfolio values by trader
    """
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT trader, portfolio_value 
                FROM portfolio_snapshots 
                WHERE (trader, timestamp) IN (
                    SELECT trader, MAX(timestamp) 
                    FROM portfolio_snapshots 
                    GROUP BY trader
                )
            ''')
            
            return dict(cursor.fetchall())
    except Exception as e:
        print(f"Latest portfolio values error: {e}")
        return {}

# =============================================================================
# MAINTENANCE FUNCTIONS (NEW)
# =============================================================================

def cleanup_old_data(log_days: int = 30, portfolio_days: int = 90) -> Dict[str, int]:
    """
    Clean up old data to prevent database bloat.
    
    Args:
        log_days (int): Keep logs for this many days
        portfolio_days (int): Keep portfolio snapshots for this many days
        
    Returns:
        dict: Statistics about cleaned up data
    """
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            
            # Calculate thresholds
            log_threshold = datetime.now() - timedelta(days=log_days)
            portfolio_threshold = datetime.now() - timedelta(days=portfolio_days)
            
            # Clean old logs
            cursor.execute('DELETE FROM logs WHERE timestamp < ?', (log_threshold.isoformat(),))
            logs_deleted = cursor.rowcount
            
            # Clean old portfolio snapshots
            cursor.execute('DELETE FROM portfolio_snapshots WHERE timestamp < ?', (portfolio_threshold.isoformat(),))
            snapshots_deleted = cursor.rowcount
            
            conn.commit()
            
            return {
                'logs_deleted': logs_deleted,
                'snapshots_deleted': snapshots_deleted,
                'cleanup_date': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Cleanup error: {e}")
        return {'error': str(e)}

def get_database_stats() -> Dict[str, Any]:
    """
    Get database statistics for monitoring.
    
    Returns:
        dict: Database statistics and health information
    """
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            
            # Get table counts
            cursor.execute('SELECT COUNT(*) FROM logs')
            log_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM portfolio_snapshots')
            snapshot_count = cursor.fetchone()[0]
            
            # Get date ranges
            cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM logs')
            log_range = cursor.fetchone()
            
            cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM portfolio_snapshots')
            snapshot_range = cursor.fetchone()
            
            # Get trader activity
            cursor.execute('SELECT trader, COUNT(*) FROM logs GROUP BY trader')
            trader_activity = dict(cursor.fetchall())
            
            return {
                'log_count': log_count,
                'snapshot_count': snapshot_count,
                'log_date_range': {'oldest': log_range[0], 'newest': log_range[1]},
                'snapshot_date_range': {'oldest': snapshot_range[0], 'newest': snapshot_range[1]},
                'trader_activity': trader_activity,
                'database_file': DB,
                'stats_generated': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Stats error: {e}")
        return {'error': str(e)}