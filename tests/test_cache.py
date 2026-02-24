"""
Cache Tests
Tests for Redis caching functionality
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.cache.redis_client import RedisClient, redis_client
from app.cache.cache_service import ProductCacheService, product_cache


class TestRedisClient:
    """Tests for Redis client"""
    
    @pytest.mark.asyncio
    async def test_get_success(self):
        """Test getting value from cache"""
        client = RedisClient()
        client._client = AsyncMock()
        client._connected = True  # Set connected flag
        client._client.get.return_value = '{"key": "value"}'
        
        result = await client.get("test_key")
        
        assert result == {"key": "value"}
        client._client.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test getting non-existent key"""
        client = RedisClient()
        client._client = AsyncMock()
        client._connected = True  # Set connected flag
        client._client.get.return_value = None
        
        result = await client.get("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_success(self):
        """Test setting value in cache"""
        client = RedisClient()
        client._client = AsyncMock()
        client._connected = True  # Set connected flag
        client._client.set.return_value = True
        
        result = await client.set("test_key", {"data": "value"}, expire=300)
        
        assert result is True
        client._client.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_success(self):
        """Test deleting key from cache"""
        client = RedisClient()
        client._client = AsyncMock()
        client._connected = True  # Set connected flag
        client._client.delete.return_value = 1
        
        result = await client.delete("test_key")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_pattern(self):
        """Test deleting keys by pattern"""
        client = RedisClient()
        client._client = AsyncMock()
        client._connected = True  # Set connected flag
        client._client.keys.return_value = ["key1", "key2", "key3"]
        client._client.delete.return_value = 3
        
        result = await client.delete_pattern("test:*")
        
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_exists(self):
        """Test checking key existence"""
        client = RedisClient()
        client._client = AsyncMock()
        client._connected = True  # Set connected flag
        client._client.exists.return_value = 1
        
        result = await client.exists("test_key")
        
        assert result is True


class TestProductCacheService:
    """Tests for product cache service"""
    
    @pytest.mark.asyncio
    async def test_set_and_get_product_detail(self):
        """Test caching and retrieving product detail"""
        service = ProductCacheService()
        
        with patch.object(redis_client, 'get', new_callable=AsyncMock) as mock_get, \
             patch.object(redis_client, 'set', new_callable=AsyncMock) as mock_set:
            
            product_data = {
                "id": "test-id",
                "name": "Test Product",
                "price": 19.99
            }
            
            # Set product
            await service.set_product_detail("test-id", product_data)
            mock_set.assert_called_once()
            
            # Get product
            mock_get.return_value = product_data
            result = await service.get_product_detail("test-id")
            
            assert result == product_data
    
    @pytest.mark.asyncio
    async def test_invalidate_product(self):
        """Test invalidating product cache"""
        service = ProductCacheService()
        
        with patch.object(redis_client, 'delete', new_callable=AsyncMock) as mock_delete, \
             patch.object(redis_client, 'delete_pattern', new_callable=AsyncMock) as mock_delete_pattern:
            
            mock_delete.return_value = True
            mock_delete_pattern.return_value = 5
            
            await service.invalidate_product("test-id")
            
            # Should delete detail and all list/search caches
            mock_delete.assert_called_once()
            assert mock_delete_pattern.call_count == 2
    
    @pytest.mark.asyncio
    async def test_hash_filters(self):
        """Test filter hashing"""
        filters1 = {"category": "Electronics", "min_price": 10}
        filters2 = {"category": "Electronics", "min_price": 10}
        filters3 = {"category": "Books"}
        
        hash1 = ProductCacheService._hash_filters(filters1)
        hash2 = ProductCacheService._hash_filters(filters2)
        hash3 = ProductCacheService._hash_filters(filters3)
        
        # Same filters should produce same hash
        assert hash1 == hash2
        # Different filters should produce different hash
        assert hash1 != hash3
        # Empty filters should return "all"
        assert ProductCacheService._hash_filters({}) == "all"
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation"""
        service = ProductCacheService()
        
        # List key
        list_key = service._list_key(1, 10, "abc123")
        assert list_key == "products:list:1:10:abc123"
        
        # Detail key
        detail_key = service._detail_key("product-uuid")
        assert detail_key == "products:detail:product-uuid"
        
        # Search key
        import hashlib
        query_hash = hashlib.md5("test query".encode()).hexdigest()[:8]
        search_key = service._search_key("test query", 1, 10)
        assert query_hash in search_key