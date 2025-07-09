"""Common dependencies."""

from typing import Optional, Tuple

from fastapi import Query

from core.config import settings


async def get_pagination_params(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Number of items to return",
    ),
) -> Tuple[int, int]:
    """
    Get pagination parameters.
    
    Args:
        skip: Number of items to skip
        limit: Number of items to return
        
    Returns:
        Tuple of (skip, limit)
    """
    return skip, limit