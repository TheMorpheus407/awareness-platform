"""Centralized cache service for managing application caching."""

from datetime import timedelta
from typing import Any, List, Optional, Dict
from uuid import UUID

from core.cache import cache
from core.cache_decorators import cache_pattern_invalidate, cache_result
from core.logging import logger


class CacheService:
    """Service for managing application-wide caching strategies."""
    
    # Cache key patterns
    PATTERNS = {
        "user": "user:{user_id}:*",
        "course": "course:{course_id}:*",
        "company": "company:{company_id}:*",
        "analytics": "analytics:*",
        "leaderboard": "leaderboard:*",
        "quiz": "quiz:{quiz_id}:*",
        "progress": "progress:user:{user_id}:*",
        "enrollment": "enrollment:user:{user_id}:*",
        "certificate": "certificate:{certificate_id}",
        "phishing": "phishing:*",
        "campaign": "campaign:{campaign_id}:*"
    }
    
    # Cache TTLs
    TTL = {
        "short": 300,      # 5 minutes
        "medium": 900,     # 15 minutes
        "long": 3600,      # 1 hour
        "very_long": 7200, # 2 hours
        "daily": 86400     # 24 hours
    }
    
    @staticmethod
    def get_user_cache_key(user_id: UUID, suffix: str = "") -> str:
        """Generate user-specific cache key."""
        base_key = f"user:{user_id}"
        return f"{base_key}:{suffix}" if suffix else base_key
    
    @staticmethod
    def get_course_cache_key(course_id: UUID, suffix: str = "") -> str:
        """Generate course-specific cache key."""
        base_key = f"course:{course_id}"
        return f"{base_key}:{suffix}" if suffix else base_key
    
    @staticmethod
    def get_company_cache_key(company_id: UUID, suffix: str = "") -> str:
        """Generate company-specific cache key."""
        base_key = f"company:{company_id}"
        return f"{base_key}:{suffix}" if suffix else base_key
    
    @staticmethod
    async def invalidate_user_cache(user_id: UUID) -> int:
        """Invalidate all cache entries for a specific user."""
        pattern = CacheService.PATTERNS["user"].format(user_id=user_id)
        count = await cache.clear_pattern(pattern)
        logger.info(f"Invalidated {count} cache entries for user {user_id}")
        return count
    
    @staticmethod
    async def invalidate_course_cache(course_id: UUID) -> int:
        """Invalidate all cache entries for a specific course."""
        pattern = CacheService.PATTERNS["course"].format(course_id=course_id)
        count = await cache.clear_pattern(pattern)
        logger.info(f"Invalidated {count} cache entries for course {course_id}")
        return count
    
    @staticmethod
    async def invalidate_company_cache(company_id: UUID) -> int:
        """Invalidate all cache entries for a specific company."""
        pattern = CacheService.PATTERNS["company"].format(company_id=company_id)
        count = await cache.clear_pattern(pattern)
        logger.info(f"Invalidated {count} cache entries for company {company_id}")
        return count
    
    @staticmethod
    async def invalidate_analytics_cache() -> int:
        """Invalidate all analytics cache entries."""
        pattern = CacheService.PATTERNS["analytics"]
        count = await cache.clear_pattern(pattern)
        logger.info(f"Invalidated {count} analytics cache entries")
        return count
    
    @staticmethod
    async def invalidate_leaderboard_cache() -> int:
        """Invalidate all leaderboard cache entries."""
        pattern = CacheService.PATTERNS["leaderboard"]
        count = await cache.clear_pattern(pattern)
        logger.info(f"Invalidated {count} leaderboard cache entries")
        return count
    
    @staticmethod
    async def warm_cache_for_user(user_id: UUID, data: Dict[str, Any]) -> None:
        """Pre-warm cache with user data."""
        # Cache user profile
        if "profile" in data:
            key = CacheService.get_user_cache_key(user_id, "profile")
            await cache.set(key, data["profile"], CacheService.TTL["medium"])
        
        # Cache user courses
        if "courses" in data:
            key = CacheService.get_user_cache_key(user_id, "courses")
            await cache.set(key, data["courses"], CacheService.TTL["medium"])
        
        # Cache user progress
        if "progress" in data:
            key = CacheService.get_user_cache_key(user_id, "progress")
            await cache.set(key, data["progress"], CacheService.TTL["short"])
        
        logger.info(f"Warmed cache for user {user_id}")
    
    @staticmethod
    async def warm_cache_for_course(course_id: UUID, data: Dict[str, Any]) -> None:
        """Pre-warm cache with course data."""
        # Cache course details
        if "details" in data:
            key = CacheService.get_course_cache_key(course_id, "details")
            await cache.set(key, data["details"], CacheService.TTL["long"])
        
        # Cache course modules
        if "modules" in data:
            key = CacheService.get_course_cache_key(course_id, "modules")
            await cache.set(key, data["modules"], CacheService.TTL["long"])
        
        # Cache course analytics
        if "analytics" in data:
            key = CacheService.get_course_cache_key(course_id, "analytics")
            await cache.set(key, data["analytics"], CacheService.TTL["medium"])
        
        logger.info(f"Warmed cache for course {course_id}")
    
    @staticmethod
    async def get_or_set(
        key: str,
        fetch_func: Any,
        expire: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """Get from cache or fetch and set if not exists."""
        # Try to get from cache
        cached_value = await cache.get(key)
        if cached_value is not None:
            return cached_value
        
        # Fetch from source
        value = await fetch_func(*args, **kwargs)
        
        # Cache the result
        if value is not None:
            await cache.set(key, value, expire or CacheService.TTL["medium"])
        
        return value
    
    @staticmethod
    async def increment_counter(key: str, amount: int = 1, expire: Optional[int] = None) -> int:
        """Increment a counter in cache."""
        new_value = await cache.incr(key, amount)
        
        # Set expiration if specified and this is a new key
        if expire and new_value == amount:
            await cache.expire(key, expire)
        
        return new_value
    
    @staticmethod
    async def get_cache_stats() -> Dict[str, Any]:
        """Get cache statistics."""
        # This would need Redis INFO command support
        # For now, return basic stats
        return {
            "status": "connected",
            "backend": "redis",
            # Add more stats as needed
        }
    
    @staticmethod
    async def clear_all_cache() -> int:
        """Clear all cache entries (use with caution!)."""
        count = await cache.clear_pattern("*")
        logger.warning(f"Cleared all {count} cache entries")
        return count


# Cache invalidation decorators for common mutations

def invalidate_user_on_update(user_id_param: str = "user_id"):
    """Decorator to invalidate user cache after updates."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Extract user_id from parameters
            user_id = kwargs.get(user_id_param)
            if not user_id:
                # Try to get from positional args
                for arg in args:
                    if hasattr(arg, 'id') and hasattr(arg, 'email'):  # User object
                        user_id = arg.id
                        break
            
            if user_id:
                await CacheService.invalidate_user_cache(user_id)
            
            return result
        return wrapper
    return decorator


def invalidate_course_on_update(course_id_param: str = "course_id"):
    """Decorator to invalidate course cache after updates."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Extract course_id
            course_id = kwargs.get(course_id_param)
            if course_id:
                await CacheService.invalidate_course_cache(course_id)
            
            return result
        return wrapper
    return decorator


def invalidate_analytics_on_update():
    """Decorator to invalidate analytics cache after updates."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            await CacheService.invalidate_analytics_cache()
            return result
        return wrapper
    return decorator