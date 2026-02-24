"""
Cache Package
Exports Redis client and cache services
"""
from .redis_client import redis_client, get_redis, RedisClient
from .cache_service import product_cache, ProductCacheService

__all__ = [
    "redis_client",
    "get_redis",
    "RedisClient",
    "product_cache",
    "ProductCacheService",
]
