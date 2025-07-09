"""Redis cache configuration and utilities."""

import json
import pickle
from datetime import timedelta
from typing import Any, Callable, Optional, Union

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from core.config import settings
from core.logging import logger
from core.monitoring import track_cache_hit, track_cache_miss


class CacheBackend:
    """Redis cache backend with async support."""
    
    def __init__(self):
        """Initialize cache backend."""
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_POOL_SIZE,
                decode_responses=settings.REDIS_DECODE_RESPONSES,
            )
            self._client = redis.Redis(connection_pool=self._pool)
            await self._client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Disconnected from Redis cache")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            if not self._client:
                return default
            
            value = await self._client.get(key)
            if value is None:
                track_cache_miss()
                return default
            
            track_cache_hit()
            
            # Try to deserialize JSON first, fall back to pickle
            if isinstance(value, bytes):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return pickle.loads(value)
            else:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds or timedelta
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._client:
                return False
            
            # Convert timedelta to seconds
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            
            # Serialize value
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)
            
            # Set with optional expiration
            if expire:
                await self._client.setex(key, expire, serialized)
            else:
                await self._client.set(key, serialized)
            
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._client:
                return False
            
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if exists, False otherwise
        """
        try:
            if not self._client:
                return False
            
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Cache key
            seconds: Expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._client:
                return False
            
            return await self._client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        Get time to live for a key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -2 if key doesn't exist, -1 if no TTL
        """
        try:
            if not self._client:
                return -2
            
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -2
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value or None if error
        """
        try:
            if not self._client:
                return None
            
            return await self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache incr error for key {key}: {e}")
            return None
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Pattern to match (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            if not self._client:
                return 0
            
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0


# Global cache instance
cache = CacheBackend()


def cache_key(*args: Any) -> str:
    """
    Generate cache key from arguments.
    
    Args:
        *args: Arguments to build key from
        
    Returns:
        Cache key string
    """
    return ":".join(str(arg) for arg in args)


def cached(
    expire: Optional[Union[int, timedelta]] = 300,
    key_prefix: Optional[str] = None,
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching function results.
    
    Args:
        expire: Expiration time in seconds or timedelta
        key_prefix: Prefix for cache key
        key_builder: Custom key builder function
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key_str = key_builder(*args, **kwargs)
            else:
                # Default key builder
                func_name = func.__name__
                if key_prefix:
                    parts = [key_prefix, func_name]
                else:
                    parts = [func_name]
                
                # Add args and kwargs to key
                if args:
                    parts.extend(str(arg) for arg in args)
                if kwargs:
                    parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                
                cache_key_str = cache_key(*parts)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key_str)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key_str, result, expire)
            
            return result
        
        return wrapper
    return decorator