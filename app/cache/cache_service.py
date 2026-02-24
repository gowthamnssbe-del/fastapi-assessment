"""
Product Cache Service
Handles caching logic for product operations
"""
from typing import Optional, List, Dict, Any
from .redis_client import redis_client
from ..core.config import settings
import json


class ProductCacheService:
    """
    Service for caching product data
    
    Cache Keys:
    - products:list:{page}:{page_size}:{filters_hash} - Paginated product lists
    - products:detail:{product_id} - Individual product details
    - products:search:{query_hash} - Search results
    """
    
    PREFIX = "products"
    
    @staticmethod
    def _list_key(page: int, page_size: int, filters_hash: str = "all") -> str:
        """Generate cache key for product list"""
        return f"{ProductCacheService.PREFIX}:list:{page}:{page_size}:{filters_hash}"
    
    @staticmethod
    def _detail_key(product_id: str) -> str:
        """Generate cache key for product detail"""
        return f"{ProductCacheService.PREFIX}:detail:{product_id}"
    
    @staticmethod
    def _search_key(query: str, page: int, page_size: int) -> str:
        """Generate cache key for search results"""
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"{ProductCacheService.PREFIX}:search:{query_hash}:{page}:{page_size}"
    
    async def get_product_list(self, page: int, page_size: int, filters: Optional[Dict] = None) -> Optional[Dict]:
        """
        Get cached product list
        
        Args:
            page: Page number
            page_size: Items per page
            filters: Applied filters
        
        Returns:
            Cached data or None
        """
        filters_hash = self._hash_filters(filters or {})
        key = self._list_key(page, page_size, filters_hash)
        return await redis_client.get(key)
    
    async def set_product_list(self, page: int, page_size: int, data: Dict, filters: Optional[Dict] = None) -> bool:
        """
        Cache product list
        
        Args:
            page: Page number
            page_size: Items per page
            data: Data to cache
            filters: Applied filters
        
        Returns:
            Success status
        """
        filters_hash = self._hash_filters(filters or {})
        key = self._list_key(page, page_size, filters_hash)
        return await redis_client.set(key, data)
    
    async def get_product_detail(self, product_id: str) -> Optional[Dict]:
        """
        Get cached product detail
        
        Args:
            product_id: Product UUID
        
        Returns:
            Cached data or None
        """
        key = self._detail_key(product_id)
        return await redis_client.get(key)
    
    async def set_product_detail(self, product_id: str, data: Dict) -> bool:
        """
        Cache product detail
        
        Args:
            product_id: Product UUID
            data: Data to cache
        
        Returns:
            Success status
        """
        key = self._detail_key(product_id)
        return await redis_client.set(key, data)
    
    async def get_search_results(self, query: str, page: int, page_size: int) -> Optional[Dict]:
        """
        Get cached search results
        
        Args:
            query: Search query
            page: Page number
            page_size: Items per page
        
        Returns:
            Cached data or None
        """
        key = self._search_key(query, page, page_size)
        return await redis_client.get(key)
    
    async def set_search_results(self, query: str, page: int, page_size: int, data: Dict) -> bool:
        """
        Cache search results
        
        Args:
            query: Search query
            page: Page number
            page_size: Items per page
            data: Data to cache
        
        Returns:
            Success status
        """
        key = self._search_key(query, page, page_size)
        return await redis_client.set(key, data)
    
    async def invalidate_product(self, product_id: str) -> None:
        """
        Invalidate all cache entries for a product
        
        Args:
            product_id: Product UUID
        """
        # Delete product detail cache
        await redis_client.delete(self._detail_key(product_id))
        
        # Invalidate all list caches
        await redis_client.delete_pattern(f"{self.PREFIX}:list:*")
        
        # Invalidate all search caches
        await redis_client.delete_pattern(f"{self.PREFIX}:search:*")
    
    async def invalidate_all_lists(self) -> None:
        """Invalidate all list and search caches"""
        await redis_client.delete_pattern(f"{self.PREFIX}:list:*")
        await redis_client.delete_pattern(f"{self.PREFIX}:search:*")
    
    @staticmethod
    def _hash_filters(filters: Dict) -> str:
        """Generate hash from filter dictionary"""
        if not filters:
            return "all"
        import hashlib
        from decimal import Decimal
        
        # Convert Decimal to float for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(v) for v in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        serializable_filters = convert_decimals(filters)
        filter_str = json.dumps(serializable_filters, sort_keys=True)
        return hashlib.md5(filter_str.encode()).hexdigest()[:8]


# Global cache service instance
product_cache = ProductCacheService()