# Compatibility layer for aioredis
from redis import asyncio as aioredis

# Re-export what we need
Redis = aioredis.Redis
from_url = aioredis.from_url

__all__ = ['Redis', 'from_url']