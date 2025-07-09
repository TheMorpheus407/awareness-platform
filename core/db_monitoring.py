"""Database monitoring and query performance tracking."""

import time
import functools
from typing import Any, Callable, Optional
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool
from loguru import logger

from core.monitoring import db_query_duration, monitored_db_query
from core.logging import log_performance_issue


class DatabaseMonitor:
    """Monitor database performance and connection pool."""
    
    def __init__(self):
        self.slow_query_threshold = 0.5  # 500ms
        self.query_stats = {}
    
    def setup_listeners(self, engine: Engine):
        """Set up SQLAlchemy event listeners for monitoring."""
        # Monitor query execution time
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
            logger.debug(f"Query started: {statement[:100]}...")
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)
            
            # Track metrics
            query_type = self._get_query_type(statement)
            db_query_duration.labels(query_type=query_type).observe(total)
            
            # Log slow queries
            if total > self.slow_query_threshold:
                log_performance_issue(
                    "slow_query",
                    total,
                    query=statement[:200],
                    query_type=query_type,
                    parameters=str(parameters)[:100] if parameters else None
                )
                
                logger.warning(
                    f"Slow query detected ({total:.2f}s): {statement[:100]}...",
                    extra={
                        "performance": True,
                        "query_time": total,
                        "query": statement,
                        "query_type": query_type
                    }
                )
        
        # Monitor connection pool
        @event.listens_for(Pool, "connect")
        def pool_connect(dbapi_conn, connection_record):
            logger.debug("New database connection created")
        
        @event.listens_for(Pool, "checkout")
        def pool_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(Pool, "checkin")
        def pool_checkin(dbapi_conn, connection_record):
            logger.debug("Connection returned to pool")
    
    def _get_query_type(self, statement: str) -> str:
        """Determine query type from SQL statement."""
        statement_upper = statement.strip().upper()
        
        if statement_upper.startswith("SELECT"):
            return "select"
        elif statement_upper.startswith("INSERT"):
            return "insert"
        elif statement_upper.startswith("UPDATE"):
            return "update"
        elif statement_upper.startswith("DELETE"):
            return "delete"
        elif statement_upper.startswith("CREATE"):
            return "create"
        elif statement_upper.startswith("ALTER"):
            return "alter"
        elif statement_upper.startswith("DROP"):
            return "drop"
        else:
            return "other"


# Global database monitor instance
db_monitor = DatabaseMonitor()


def monitor_query(query_name: str = None):
    """
    Decorator for monitoring database query performance.
    
    Usage:
        @monitor_query("get_user_by_email")
        async def get_user_by_email(db: AsyncSession, email: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = query_name or f"{func.__module__}.{func.__name__}"
            
            async with monitored_db_query(name):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = query_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                db_query_duration.labels(query_type=name).observe(duration)
                
                if duration > db_monitor.slow_query_threshold:
                    logger.warning(
                        f"Slow query '{name}' took {duration:.2f}s"
                    )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Query '{name}' failed after {duration:.2f}s: {e}"
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


class QueryAnalyzer:
    """Analyze query patterns and suggest optimizations."""
    
    def __init__(self):
        self.query_patterns = {}
        self.optimization_suggestions = []
    
    def analyze_slow_queries(self, queries: list) -> list:
        """Analyze slow queries and provide optimization suggestions."""
        suggestions = []
        
        for query in queries:
            # Check for missing indexes
            if "WHERE" in query and "INDEX" not in query:
                suggestions.append({
                    "type": "missing_index",
                    "query": query,
                    "suggestion": "Consider adding an index on the WHERE clause columns"
                })
            
            # Check for SELECT *
            if "SELECT *" in query:
                suggestions.append({
                    "type": "select_star",
                    "query": query,
                    "suggestion": "Avoid SELECT *, specify only needed columns"
                })
            
            # Check for N+1 queries
            if self._detect_n_plus_one(query):
                suggestions.append({
                    "type": "n_plus_one",
                    "query": query,
                    "suggestion": "Use eager loading or joins to avoid N+1 queries"
                })
        
        return suggestions
    
    def _detect_n_plus_one(self, query: str) -> bool:
        """Detect potential N+1 query patterns."""
        # Simple heuristic: multiple similar queries in short time
        query_pattern = self._get_query_pattern(query)
        
        if query_pattern not in self.query_patterns:
            self.query_patterns[query_pattern] = {
                "count": 0,
                "last_seen": time.time()
            }
        
        pattern_info = self.query_patterns[query_pattern]
        current_time = time.time()
        
        # If similar query executed multiple times within 1 second
        if current_time - pattern_info["last_seen"] < 1:
            pattern_info["count"] += 1
            if pattern_info["count"] > 10:
                return True
        else:
            pattern_info["count"] = 1
        
        pattern_info["last_seen"] = current_time
        return False
    
    def _get_query_pattern(self, query: str) -> str:
        """Extract query pattern by removing specific values."""
        import re
        
        # Remove quoted strings
        pattern = re.sub(r"'[^']*'", "'?'", query)
        # Remove numbers
        pattern = re.sub(r'\b\d+\b', '?', pattern)
        
        return pattern


# Export utilities
__all__ = [
    "DatabaseMonitor",
    "db_monitor",
    "monitor_query",
    "QueryAnalyzer",
]