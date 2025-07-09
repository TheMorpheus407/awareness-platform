"""Database monitoring utilities."""

import asyncio
import time
from typing import Any, Dict, List, Optional

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import Pool

from core.logging import logger
from prometheus_client import Counter, Gauge, Histogram

from core.monitoring import DATABASE_CONNECTIONS

# Additional database metrics
DB_QUERY_DURATION = Histogram(
    "database_query_duration_seconds",
    "Database query execution time",
    ["query_type", "table"]
)

DB_QUERY_COUNT = Counter(
    "database_queries_total",
    "Total database queries",
    ["query_type", "table"]
)

DB_CONNECTION_ERRORS = Counter(
    "database_connection_errors_total",
    "Total database connection errors"
)

DB_TRANSACTION_COUNT = Counter(
    "database_transactions_total",
    "Total database transactions",
    ["status"]
)

DB_POOL_SIZE = Gauge(
    "database_pool_size",
    "Database connection pool size"
)

DB_POOL_CHECKED_OUT = Gauge(
    "database_pool_checked_out",
    "Database connections checked out from pool"
)

DB_POOL_OVERFLOW = Gauge(
    "database_pool_overflow",
    "Database pool overflow connections"
)


class DatabaseMonitor:
    """Database monitoring utilities."""
    
    def __init__(self):
        """Initialize database monitor."""
        self.slow_query_threshold = 1.0  # seconds
        self.query_stats: Dict[str, Dict[str, Any]] = {}
    
    def setup_engine_monitoring(self, engine: Engine) -> None:
        """
        Set up monitoring for a database engine.
        
        Args:
            engine: SQLAlchemy engine to monitor
        """
        # Monitor connection pool
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Track new connections."""
            connection_record.info['connect_time'] = time.time()
            logger.debug("New database connection established")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Track connection checkouts."""
            checkout_time = time.time()
            connection_record.info['checkout_time'] = checkout_time
            self._update_pool_metrics(engine.pool)
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Track connection checkins."""
            checkin_time = time.time()
            checkout_time = connection_record.info.get('checkout_time', checkin_time)
            duration = checkin_time - checkout_time
            
            if duration > 30:  # Log long-held connections
                logger.warning(f"Connection held for {duration:.2f} seconds")
            
            self._update_pool_metrics(engine.pool)
        
        # Monitor queries
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query start."""
            context._query_start_time = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query completion."""
            duration = time.time() - context._query_start_time
            
            # Parse query type and table
            query_type, table = self._parse_query(statement)
            
            # Update metrics
            DB_QUERY_DURATION.labels(query_type=query_type, table=table).observe(duration)
            DB_QUERY_COUNT.labels(query_type=query_type, table=table).inc()
            
            # Log slow queries
            if duration > self.slow_query_threshold:
                logger.warning(
                    f"Slow query detected ({duration:.2f}s): {statement[:100]}...",
                    extra={
                        "query_type": query_type,
                        "table": table,
                        "duration": duration,
                        "statement": statement[:500],
                    }
                )
            
            # Update query stats
            self._update_query_stats(query_type, table, duration)
        
        @event.listens_for(engine, "handle_error")
        def handle_error(exception_context):
            """Track database errors."""
            DB_CONNECTION_ERRORS.inc()
            logger.error(
                f"Database error: {exception_context.original_exception}",
                exc_info=exception_context.original_exception
            )
        
        # Initial pool metrics
        self._update_pool_metrics(engine.pool)
        logger.info("Database monitoring configured")
    
    def _parse_query(self, statement: str) -> tuple[str, str]:
        """
        Parse query to extract type and table name.
        
        Args:
            statement: SQL statement
            
        Returns:
            Tuple of (query_type, table_name)
        """
        statement_upper = statement.strip().upper()
        
        # Determine query type
        if statement_upper.startswith("SELECT"):
            query_type = "SELECT"
        elif statement_upper.startswith("INSERT"):
            query_type = "INSERT"
        elif statement_upper.startswith("UPDATE"):
            query_type = "UPDATE"
        elif statement_upper.startswith("DELETE"):
            query_type = "DELETE"
        elif statement_upper.startswith("CREATE"):
            query_type = "CREATE"
        elif statement_upper.startswith("DROP"):
            query_type = "DROP"
        elif statement_upper.startswith("ALTER"):
            query_type = "ALTER"
        else:
            query_type = "OTHER"
        
        # Try to extract table name
        table = "unknown"
        try:
            if query_type in ["SELECT", "DELETE"]:
                # Look for FROM clause
                from_index = statement_upper.find("FROM")
                if from_index != -1:
                    after_from = statement[from_index + 4:].strip()
                    table = after_from.split()[0].strip('"').strip("'").lower()
            elif query_type in ["INSERT", "UPDATE"]:
                # Look for INTO or UPDATE clause
                parts = statement_upper.split()
                if len(parts) > 2:
                    table = parts[2].strip('"').strip("'").lower()
        except Exception:
            pass
        
        return query_type, table
    
    def _update_pool_metrics(self, pool: Pool) -> None:
        """Update connection pool metrics."""
        try:
            DB_POOL_SIZE.set(pool.size())
            DB_POOL_CHECKED_OUT.set(pool.checked_out())
            DB_POOL_OVERFLOW.set(pool.overflow())
            DATABASE_CONNECTIONS.set(pool.size() + pool.overflow())
        except Exception as e:
            logger.error(f"Error updating pool metrics: {e}")
    
    def _update_query_stats(self, query_type: str, table: str, duration: float) -> None:
        """Update internal query statistics."""
        key = f"{query_type}:{table}"
        
        if key not in self.query_stats:
            self.query_stats[key] = {
                "count": 0,
                "total_duration": 0,
                "min_duration": float('inf'),
                "max_duration": 0,
            }
        
        stats = self.query_stats[key]
        stats["count"] += 1
        stats["total_duration"] += duration
        stats["min_duration"] = min(stats["min_duration"], duration)
        stats["max_duration"] = max(stats["max_duration"], duration)
    
    def get_query_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get query statistics.
        
        Returns:
            Dictionary of query statistics
        """
        result = {}
        for key, stats in self.query_stats.items():
            avg_duration = stats["total_duration"] / stats["count"] if stats["count"] > 0 else 0
            result[key] = {
                **stats,
                "avg_duration": avg_duration,
            }
        return result
    
    async def check_database_health(self, session: Session) -> Dict[str, Any]:
        """
        Check database health.
        
        Args:
            session: Database session
            
        Returns:
            Health check results
        """
        health = {
            "status": "healthy",
            "checks": {},
            "metrics": {},
        }
        
        try:
            # Basic connectivity check
            start = time.time()
            result = session.execute(text("SELECT 1"))
            result.scalar()
            health["checks"]["connectivity"] = {
                "status": "ok",
                "latency_ms": (time.time() - start) * 1000,
            }
            
            # Check table counts
            tables = ["users", "companies", "courses", "enrollments"]
            for table in tables:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    health["metrics"][f"{table}_count"] = count
                except Exception as e:
                    health["checks"][f"{table}_accessible"] = {
                        "status": "error",
                        "error": str(e),
                    }
            
            # Check connection pool
            if hasattr(session.bind, "pool"):
                pool = session.bind.pool
                health["metrics"]["pool_size"] = pool.size()
                health["metrics"]["pool_checked_out"] = pool.checked_out()
                health["metrics"]["pool_overflow"] = pool.overflow()
            
            # Add query stats
            health["metrics"]["query_stats"] = self.get_query_stats()
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
            logger.error(f"Database health check failed: {e}")
        
        return health


# Global database monitor instance
db_monitor = DatabaseMonitor()


def track_transaction(status: str = "committed"):
    """
    Track a database transaction.
    
    Args:
        status: Transaction status (committed, rolled_back, failed)
    """
    DB_TRANSACTION_COUNT.labels(status=status).inc()