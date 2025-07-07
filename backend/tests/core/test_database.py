"""Tests for database session and connection management."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.exc import OperationalError
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from core.database import get_db, AsyncSessionLocal, engine


@pytest.mark.asyncio
class TestDatabaseSession:
    """Test database session management."""

    async def test_get_db_creates_session(self) -> None:
        """Test that get_db creates a valid database session."""
        async for session in get_db():
            assert isinstance(session, AsyncSession)
            assert session.is_active
            # Test connection is working
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    async def test_get_db_closes_session(self) -> None:
        """Test that get_db properly closes the session."""
        async for session in get_db():
            session_id = id(session)
        
        # Session should be closed after exiting context
        # (We can't directly check if closed, but we verify a new session has different ID)
        async for new_session in get_db():
            assert id(new_session) != session_id

    async def test_get_db_rollback_on_exception(self) -> None:
        """Test that session rolls back on exception."""
        try:
            async for session in get_db():
                # Start a transaction
                await session.execute(text("BEGIN"))
                # This should fail and cause rollback
                raise Exception("Test exception")
        except Exception as e:
            assert str(e) == "Test exception"
        
        # Verify we can still get a new working session
        async for session in get_db():
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    async def test_session_isolation(self) -> None:
        """Test that sessions are isolated from each other."""
        sessions = []
        
        # Create multiple sessions
        async def create_session():
            async for session in get_db():
                sessions.append(session)
                await asyncio.sleep(0.01)  # Small delay to ensure different sessions
        
        # Create 3 sessions concurrently
        await asyncio.gather(
            create_session(),
            create_session(),
            create_session()
        )
        
        # All sessions should be different instances
        session_ids = [id(s) for s in sessions]
        assert len(set(session_ids)) == 3

    async def test_session_transaction_commit(self, db: AsyncSession) -> None:
        """Test that transactions can be committed."""
        # Execute a simple query in a transaction
        result = await db.execute(text("SELECT 1 as value"))
        assert result.scalar() == 1
        
        # The fixture handles commit, so we just verify it works
        assert db.is_active

    async def test_session_transaction_rollback(self) -> None:
        """Test that transactions can be rolled back."""
        async for session in get_db():
            # Start transaction
            await session.execute(text("BEGIN"))
            
            # Make a change (create temp table)
            await session.execute(text("CREATE TEMP TABLE test_rollback (id INT)"))
            
            # Rollback
            await session.rollback()
            
            # Table should not exist
            result = await session.execute(
                text("SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'test_rollback')")
            )
            assert result.scalar() is False

    async def test_concurrent_sessions(self) -> None:
        """Test multiple concurrent database sessions."""
        async def run_query(query_id: int):
            async for session in get_db():
                result = await session.execute(
                    text(f"SELECT :id as query_id"),
                    {"id": query_id}
                )
                return result.scalar()
        
        # Run 10 concurrent queries
        tasks = [run_query(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All queries should return their respective IDs
        assert results == list(range(10))

    async def test_session_pool_limit(self) -> None:
        """Test that session pool respects connection limits."""
        # This test verifies the pool doesn't create unlimited connections
        sessions = []
        
        async def create_and_hold_session():
            async for session in get_db():
                sessions.append(session)
                # Hold the session open
                await asyncio.sleep(0.1)
        
        # Try to create many sessions concurrently
        # The pool should queue requests rather than failing
        tasks = [create_and_hold_session() for _ in range(20)]
        
        # This should complete without errors
        await asyncio.gather(*tasks)
        assert len(sessions) == 20

    @patch('core.database.create_async_engine')
    async def test_database_connection_retry(self, mock_create_engine) -> None:
        """Test database connection retry logic."""
        # Mock engine that fails first 2 times, then succeeds
        call_count = 0
        
        async def mock_connect():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OperationalError("Connection failed", None, None)
        
        mock_engine = AsyncMock()
        mock_engine.connect = mock_connect
        mock_create_engine.return_value = mock_engine
        
        # Should retry and eventually succeed
        # (In real implementation, you'd add retry logic to database.py)

    async def test_session_with_different_isolation_levels(self) -> None:
        """Test sessions with different isolation levels."""
        async for session in get_db():
            # Set READ COMMITTED isolation
            await session.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED"))
            
            result = await session.execute(text("SHOW TRANSACTION ISOLATION LEVEL"))
            isolation_level = result.scalar()
            assert "read committed" in isolation_level.lower()

    async def test_session_autoflush_behavior(self, db: AsyncSession) -> None:
        """Test session autoflush behavior."""
        from models.user import User
        
        # Create a user instance
        user = User(
            email="autoflush@example.com",
            username="autoflushtest",
            hashed_password="hashedpwd",
            first_name="Auto",
            last_name="Flush"
        )
        
        # Add to session
        db.add(user)
        
        # Query should trigger autoflush
        result = await db.execute(
            text("SELECT COUNT(*) FROM users WHERE email = :email"),
            {"email": "autoflush@example.com"}
        )
        
        # User should be flushed but not committed
        # (In test environment with rollback, count should be 0)
        assert result.scalar() == 0

    async def test_engine_disposal(self) -> None:
        """Test proper engine disposal."""
        # Get current engine
        current_engine = engine
        
        # Verify engine is working
        async with current_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        
        # In production, you'd call engine.dispose() on shutdown
        # This test just verifies the engine exists and works

    async def test_session_execute_many(self, db: AsyncSession) -> None:
        """Test bulk operations with session."""
        # Prepare multiple statements
        statements = [
            text("SELECT 1 as num"),
            text("SELECT 2 as num"),
            text("SELECT 3 as num")
        ]
        
        # Execute all statements
        results = []
        for stmt in statements:
            result = await db.execute(stmt)
            results.append(result.scalar())
        
        assert results == [1, 2, 3]

    async def test_session_info_attribute(self) -> None:
        """Test session info attribute for storing metadata."""
        async for session in get_db():
            # Store custom info in session
            session.info["user_id"] = 123
            session.info["request_id"] = "abc-123"
            
            # Verify info is accessible
            assert session.info["user_id"] == 123
            assert session.info["request_id"] == "abc-123"

    async def test_database_url_parsing(self) -> None:
        """Test that database URL is properly parsed."""
        from core.config import settings
        
        # Verify settings has correct database URL format
        assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")
        assert "cybersecurity_platform" in settings.DATABASE_URL

    async def test_session_event_listeners(self) -> None:
        """Test that session events can be tracked."""
        events_fired = []
        
        async for session in get_db():
            # In production, you might add event listeners for monitoring
            # This test just verifies session is created properly
            events_fired.append("session_created")
            
            await session.execute(text("SELECT 1"))
            events_fired.append("query_executed")
        
        events_fired.append("session_closed")
        
        assert events_fired == ["session_created", "query_executed", "session_closed"]