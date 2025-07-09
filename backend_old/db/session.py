"""Database session configuration."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.rls import set_rls_context, clear_rls_context

# Convert postgresql URL to postgresql+asyncpg for async support
database_url = str(settings.DATABASE_URL)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine
engine = create_async_engine(
    database_url,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Alias for backward compatibility
async_session_maker = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_with_rls(current_user=None) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with RLS context set based on current user.
    
    Args:
        current_user: The authenticated user (will be injected by FastAPI)
    
    Yields:
        AsyncSession: Database session with RLS context
    """
    async with AsyncSessionLocal() as session:
        try:
            # Set RLS context if user is provided
            if current_user:
                await set_rls_context(
                    session,
                    current_user.company_id,
                    current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
                )
            
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # Clear RLS context
            if current_user:
                await clear_rls_context(session)
            await session.close()