"""Redis caching configuration and utilities."""

import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
from functools import wraps
import hashlib

import redis.asyncio as redis
from redis.exceptions import RedisError
from fastapi import Request

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Manages Redis cache connections and operations."""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                health_check_interval=30,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 60,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                }
            )
            await self._redis.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._redis:
            return None
        
        try:
            value = await self._redis.get(key)
            if value:
                try:
                    # Try to deserialize JSON
                    return json.loads(value)
                except json.JSONDecodeError:
                    # Return as string if not JSON
                    return value
        except RedisError as e:
            logger.error(f"Redis get error: {e}")
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache with optional expiration."""
        if not self._redis:
            return False
        
        try:
            # Serialize to JSON if not string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            if expire:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())
                await self._redis.setex(key, expire, value)
            else:
                await self._redis.set(key, value)
            return True
        except RedisError as e:
            logger.error(f"Redis set error: {e}")
        return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._redis:
            return False
        
        try:
            await self._redis.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Redis delete error: {e}")
        return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self._redis:
            return 0
        
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                return await self._redis.delete(*keys)
        except RedisError as e:
            logger.error(f"Redis delete pattern error: {e}")
        return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._redis:
            return False
        
        try:
            return await self._redis.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis exists error: {e}")
        return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in cache."""
        if not self._redis:
            return None
        
        try:
            return await self._redis.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis increment error: {e}")
        return None
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get time to live for a key."""
        if not self._redis:
            return None
        
        try:
            ttl = await self._redis.ttl(key)
            return ttl if ttl >= 0 else None
        except RedisError as e:
            logger.error(f"Redis TTL error: {e}")
        return None


# Global cache instance
cache_manager = CacheManager(settings.REDIS_URL or "redis://localhost:6379")


def cache_key_wrapper(prefix: str):
    """Generate cache key with prefix."""
    def generate_key(*args, **kwargs):
        # Create a unique key from arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_data = ":".join(key_parts)
        
        # Hash if too long
        if len(key_data) > 200:
            key_data = hashlib.md5(key_data.encode()).hexdigest()
        
        return f"{prefix}:{key_data}"
    return generate_key


def cached(
    expire: Union[int, timedelta] = 3600,
    prefix: str = "cache",
    key_func: Optional[callable] = None
):
    """
    Decorator for caching function results.
    
    Args:
        expire: Cache expiration time in seconds or timedelta
        prefix: Cache key prefix
        key_func: Custom function to generate cache key
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_gen = cache_key_wrapper(f"{prefix}:{func.__name__}")
                cache_key = key_gen(*args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_manager.set(cache_key, result, expire)
            logger.debug(f"Cached result for key: {cache_key}")
            
            return result
        return wrapper
    return decorator


class RateLimiter:
    """Redis-based rate limiter."""
    
    def __init__(self, max_requests: int = 60, window: int = 60):
        self.max_requests = max_requests
        self.window = window
    
    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed."""
        key = f"rate_limit:{identifier}"
        
        try:
            current = await cache_manager.increment(key)
            
            if current == 1:
                # First request, set expiration
                await cache_manager._redis.expire(key, self.window)
            
            return current <= self.max_requests
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Allow request on error
            return True
    
    async def get_remaining(self, identifier: str) -> tuple[int, int]:
        """Get remaining requests and reset time."""
        key = f"rate_limit:{identifier}"
        
        try:
            current = await cache_manager.get(key)
            if current:
                current = int(current)
                remaining = max(0, self.max_requests - current)
                ttl = await cache_manager.get_ttl(key) or 0
                return remaining, ttl
        except Exception:
            pass
        
        return self.max_requests, 0


# Cache key generators for common use cases
def user_cache_key(user_id: Union[str, int]) -> str:
    """Generate cache key for user data."""
    return f"user:{user_id}"


def company_cache_key(company_id: Union[str, int]) -> str:
    """Generate cache key for company data."""
    return f"company:{company_id}"


def course_cache_key(course_id: Union[str, int]) -> str:
    """Generate cache key for course data."""
    return f"course:{course_id}"


def session_cache_key(session_id: str) -> str:
    """Generate cache key for session data."""
    return f"session:{session_id}"


# Cache invalidation helpers
async def invalidate_user_cache(user_id: Union[str, int]):
    """Invalidate all cache entries for a user."""
    patterns = [
        f"user:{user_id}*",
        f"*:user:{user_id}:*",
        f"session:*"  # Sessions might contain user data
    ]
    
    for pattern in patterns:
        await cache_manager.delete_pattern(pattern)


async def invalidate_company_cache(company_id: Union[str, int]):
    """Invalidate all cache entries for a company."""
    patterns = [
        f"company:{company_id}*",
        f"*:company:{company_id}:*"
    ]
    
    for pattern in patterns:
        await cache_manager.delete_pattern(pattern)


async def invalidate_course_cache(course_id: Union[str, int]):
    """Invalidate all cache entries for a course."""
    patterns = [
        f"course:{course_id}*",
        f"*:course:{course_id}:*"
    ]
    
    for pattern in patterns:
        await cache_manager.delete_pattern(pattern)