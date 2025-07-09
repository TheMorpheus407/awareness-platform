"""Common dependencies for API endpoints."""

from typing import Optional, Tuple

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db as _get_db


async def get_db() -> AsyncSession:
    """
    Get database session.
    
    Yields:
        Database session
    """
    async for session in _get_db():
        yield session


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size")
) -> Tuple[int, int]:
    """
    Get pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        size: Number of items per page
        
    Returns:
        Tuple of (offset, limit)
    """
    offset = (page - 1) * size
    return offset, size


def get_sorting_params(
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
) -> Tuple[Optional[str], str]:
    """
    Get sorting parameters.
    
    Args:
        sort_by: Field name to sort by
        sort_order: Sort order (asc/desc)
        
    Returns:
        Tuple of (sort_by, sort_order)
    """
    return sort_by, sort_order


def get_filter_params(
    search: Optional[str] = Query(None, description="Search term"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
) -> dict:
    """
    Get common filter parameters.
    
    Args:
        search: Search term
        is_active: Active status filter
        
    Returns:
        Dictionary of filter parameters
    """
    filters = {}
    
    if search is not None:
        filters["search"] = search
        
    if is_active is not None:
        filters["is_active"] = is_active
        
    return filters