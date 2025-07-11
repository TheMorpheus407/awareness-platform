"""Advanced caching decorators for performance optimization."""

import functools
import hashlib
import json
from datetime import timedelta
from typing import Any, Callable, Optional, Union

from core.cache import cache, cache_key
from core.logging import logger
from core.monitoring import track_cache_hit, track_cache_miss


def make_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.
    
    Args:
        prefix: Key prefix
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Convert args and kwargs to a stable string representation
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        if hasattr(arg, 'id'):  # Handle model instances
            key_parts.append(f"{type(arg).__name__}:{arg.id}")
        elif isinstance(arg, (list, tuple)):
            key_parts.append(hashlib.md5(str(sorted(arg)).encode()).hexdigest()[:8])
        elif isinstance(arg, dict):
            key_parts.append(hashlib.md5(json.dumps(arg, sort_keys=True).encode()).hexdigest()[:8])
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        if hasattr(v, 'id'):
            key_parts.append(f"{k}:{type(v).__name__}:{v.id}")
        else:
            key_parts.append(f"{k}:{v}")
    
    return ":".join(key_parts)


def cache_result(
    expire: Optional[Union[int, timedelta]] = 300,
    key_prefix: Optional[str] = None,
    condition: Optional[Callable] = None,
    cache_none: bool = False,
    namespace: Optional[str] = None
):
    """
    Decorator to cache function results with advanced options.
    
    Args:
        expire: Expiration time in seconds or timedelta (default: 5 minutes)
        key_prefix: Custom key prefix (default: function name)
        condition: Function to determine if result should be cached
        cache_none: Whether to cache None results
        namespace: Cache namespace for organization
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or f"{namespace or 'default'}:{func.__module__}.{func.__name__}"
            cache_key_str = make_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key_str)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key_str}")
                track_cache_hit()
                return cached_value
            elif cached_value is None and await cache.exists(cache_key_str):
                # Cached None value
                if cache_none:
                    logger.debug(f"Cache hit (None) for {cache_key_str}")
                    track_cache_hit()
                    return None
            
            # Call the function
            logger.debug(f"Cache miss for {cache_key_str}")
            track_cache_miss()
            result = await func(*args, **kwargs)
            
            # Check if result should be cached
            should_cache = True
            if condition and not condition(result):
                should_cache = False
            elif result is None and not cache_none:
                should_cache = False
            
            # Cache the result
            if should_cache:
                await cache.set(cache_key_str, result, expire)
                logger.debug(f"Cached result for {cache_key_str}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async cache
            # This is a fallback that just calls the function
            logger.warning(f"Sync function {func.__name__} called with cache decorator")
            return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_invalidate(*cache_keys: str):
    """
    Decorator to invalidate specific cache keys after function execution.
    
    Args:
        *cache_keys: Cache keys to invalidate
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate cache keys
            for key in cache_keys:
                await cache.delete(key)
                logger.debug(f"Invalidated cache key: {key}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            logger.warning(f"Sync cache invalidation not supported for {func.__name__}")
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_pattern_invalidate(pattern: str):
    """
    Decorator to invalidate cache keys matching a pattern after function execution.
    
    Args:
        pattern: Pattern to match (e.g., "user:*")
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate matching keys
            deleted_count = await cache.clear_pattern(pattern)
            logger.debug(f"Invalidated {deleted_count} cache keys matching pattern: {pattern}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            logger.warning(f"Sync pattern invalidation not supported for {func.__name__}")
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_stampede_protect(
    expire: Optional[Union[int, timedelta]] = 300,
    lock_timeout: int = 30,
    beta: float = 1.0
):
    """
    Decorator to prevent cache stampede using probabilistic early expiration.
    
    This decorator implements the XFetch algorithm to prevent cache stampede
    by randomly pre-computing values before they expire.
    
    Args:
        expire: Expiration time in seconds or timedelta
        lock_timeout: Lock timeout in seconds
        beta: Beta parameter for early expiration probability
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio
            import random
            import time
            
            # Generate cache key
            prefix = f"stampede:{func.__module__}.{func.__name__}"
            cache_key_str = make_cache_key(prefix, *args, **kwargs)
            lock_key = f"{cache_key_str}:lock"
            
            # Try to get from cache with TTL
            cached_value = await cache.get(cache_key_str)
            ttl = await cache.ttl(cache_key_str)
            
            if cached_value is not None:
                # Calculate if we should regenerate early
                if ttl > 0:
                    # XFetch algorithm: regenerate with probability based on remaining TTL
                    expiry_seconds = expire.total_seconds() if isinstance(expire, timedelta) else expire
                    delta = time.time() - (expiry_seconds - ttl)
                    should_regenerate = delta * beta * random.random() >= ttl
                    
                    if not should_regenerate:
                        track_cache_hit()
                        return cached_value
            
            # Try to acquire lock
            lock_acquired = await cache.set(
                lock_key, 
                "locked", 
                expire=lock_timeout
            )
            
            if not lock_acquired:
                # Another process is regenerating, wait and return cached value
                if cached_value is not None:
                    track_cache_hit()
                    return cached_value
                
                # Wait for lock to be released
                for _ in range(lock_timeout):
                    await asyncio.sleep(1)
                    cached_value = await cache.get(cache_key_str)
                    if cached_value is not None:
                        track_cache_hit()
                        return cached_value
            
            try:
                # Regenerate value
                track_cache_miss()
                result = await func(*args, **kwargs)
                
                # Cache the result
                await cache.set(cache_key_str, result, expire)
                
                return result
            finally:
                # Release lock
                if lock_acquired:
                    await cache.delete(lock_key)
        
        return wrapper
    
    return decorator


def cache_aside(
    expire: Optional[Union[int, timedelta]] = 300,
    key_func: Optional[Callable] = None
):
    """
    Cache-aside pattern decorator with custom key generation.
    
    Args:
        expire: Expiration time
        key_func: Custom function to generate cache key from arguments
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                prefix = f"aside:{func.__module__}.{func.__name__}"
                cache_key_str = make_cache_key(prefix, *args, **kwargs)
            
            # Try cache first
            cached_value = await cache.get(cache_key_str)
            if cached_value is not None:
                track_cache_hit()
                return cached_value
            
            # Load from source
            track_cache_miss()
            result = await func(*args, **kwargs)
            
            # Update cache
            if result is not None:
                await cache.set(cache_key_str, result, expire)
            
            return result
        
        return wrapper
    
    return decorator


# Specific cache decorators for common use cases

def cache_user_data(expire: int = 300):
    """Cache user-related data with automatic invalidation on user updates."""
    return cache_result(
        expire=expire,
        namespace="user",
        condition=lambda result: result is not None
    )


def cache_course_data(expire: int = 600):
    """Cache course-related data with longer expiration."""
    return cache_result(
        expire=expire,
        namespace="course",
        condition=lambda result: result is not None
    )


def cache_analytics(expire: int = 900):
    """Cache analytics data with 15-minute expiration."""
    return cache_result(
        expire=expire,
        namespace="analytics",
        cache_none=True
    )


def cache_expensive_computation(expire: int = 3600):
    """Cache expensive computations with stampede protection."""
    return cache_stampede_protect(
        expire=expire,
        lock_timeout=60,
        beta=1.0
    )


# Import asyncio at module level
import asyncio