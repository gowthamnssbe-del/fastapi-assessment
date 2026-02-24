"""
Redis Cache Client
Handles caching operations with connection pooling
"""
import json
from typing import Optional, Any, List
import redis.asyncio as redis
from ..core.config import settings


class RedisClient:
    """
    Redis client for caching operations
    
    Features:
    - Async operations
    - JSON serialization
    - Connection pooling
    - Graceful failure when Redis is unavailable
    """
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected: bool = False
    
    async def connect(self):
        """Establish Redis connection"""
        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._client.ping()
            self._connected = True
            print("Redis connected")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            print("Continuing without caching...")
            self._connected = False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            try:
                await self._client.close()
            except:
                pass
        self._connected = False
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Get Redis client instance"""
        return self._client if self._connected else None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._connected or not self._client:
            return None
        try:
            value = await self._client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
        except:
            pass
        return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self._connected or not self._client:
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            expire = expire or settings.CACHE_EXPIRE_SECONDS
            return await self._client.set(key, value, ex=expire)
        except:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._connected or not self._client:
            return False
        try:
            return await self._client.delete(key) > 0
        except:
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self._connected or not self._client:
            return 0
        try:
            keys = await self._client.keys(pattern)
            if keys:
                return await self._client.delete(*keys)
        except:
            pass
        return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._connected or not self._client:
            return False
        try:
            return await self._client.exists(key) > 0
        except:
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        if not self._connected or not self._client:
            return False
        try:
            return await self._client.expire(key, seconds)
        except:
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cache"""
        if not self._connected or not self._client:
            return False
        try:
            return await self._client.flushdb()
        except:
            return False


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency to get Redis client"""
    return redis_client