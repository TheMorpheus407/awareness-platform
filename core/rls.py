"""Row Level Security (RLS) utilities for multi-tenant isolation."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid


async def set_rls_context(
    session: AsyncSession,
    company_id: Optional[uuid.UUID],
    user_role: Optional[str] = None
) -> None:
    """
    Set RLS context for the current database session.
    
    This function sets PostgreSQL session variables that are used by RLS policies
    to determine data access permissions.
    
    Args:
        session: The database session
        company_id: The company ID for the current user
        user_role: The role of the current user (e.g., 'system_admin', 'company_admin')
    """
    if company_id:
        await session.execute(
            text("SET LOCAL app.current_company_id = :company_id"),
            {"company_id": str(company_id)}
        )
    
    if user_role:
        await session.execute(
            text("SET LOCAL app.current_user_role = :role"),
            {"role": user_role}
        )


async def clear_rls_context(session: AsyncSession) -> None:
    """
    Clear RLS context from the current database session.
    
    Args:
        session: The database session
    """
    await session.execute(text("RESET app.current_company_id"))
    await session.execute(text("RESET app.current_user_role"))


class RLSMiddleware:
    """
    Database middleware to automatically set RLS context based on the current user.
    
    This should be used with FastAPI dependency injection to ensure RLS is properly
    configured for each request.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clear RLS context when session ends
        await clear_rls_context(self.session)
    
    async def set_user_context(self, user):
        """Set RLS context based on user object."""
        if user:
            await set_rls_context(
                self.session,
                user.company_id if hasattr(user, 'company_id') else None,
                user.role.value if hasattr(user, 'role') else None
            )