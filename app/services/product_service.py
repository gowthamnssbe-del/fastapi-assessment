"""
Product Service
Business logic for product CRUD operations with caching
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from decimal import Decimal
import math
from uuid import UUID

from ..models.product import Product
from ..models.schemas import (
    ProductCreate, ProductUpdate, ProductFilter, ProductSort,
    PaginationParams, PaginatedResponse
)
from ..cache import product_cache


class ProductService:
    """Service for product operations with Redis caching"""
    
    @staticmethod
    async def create_product(db: AsyncSession, product_data: ProductCreate) -> Product:
        """
        Create a new product
        
        Args:
            db: Database session
            product_data: Product creation data
        
        Returns:
            Created product instance
        """
        product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            stock=product_data.stock,
            category=product_data.category,
            sku=product_data.sku
        )
        
        db.add(product)
        await db.flush()
        await db.refresh(product)
        
        # Invalidate cache after creating new product
        await product_cache.invalidate_all_lists()
        
        return product
    
    @staticmethod
    async def get_product_by_id(
        db: AsyncSession, 
        product_id: UUID,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get product by ID with optional caching
        
        Args:
            db: Database session
            product_id: Product UUID
            use_cache: Whether to use cache
        
        Returns:
            Product dictionary or None
        """
        # Try cache first
        if use_cache:
            cached = await product_cache.get_product_detail(str(product_id))
            if cached:
                return cached
        
        # Query database
        result = await db.execute(
            select(Product).where(
                Product.id == str(product_id),
                Product.is_deleted == False
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            return None
        
        # Convert to dict
        product_dict = {
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "stock": product.stock,
            "category": product.category,
            "sku": product.sku,
            "created_at": product.created_at.isoformat(),
            "updated_at": product.updated_at.isoformat(),
        }
        
        # Cache result
        if use_cache:
            await product_cache.set_product_detail(str(product_id), product_dict)
        
        return product_dict
    
    @staticmethod
    async def get_products(
        db: AsyncSession,
        pagination: PaginationParams,
        filters: Optional[ProductFilter] = None,
        sort: Optional[ProductSort] = None,
        use_cache: bool = True
    ) -> PaginatedResponse:
        """
        Get paginated products with filtering and sorting
        
        Args:
            db: Database session
            pagination: Pagination parameters
            filters: Filter parameters
            sort: Sort parameters
            use_cache: Whether to use cache
        
        Returns:
            Paginated response with products
        """
        # Build filter dict for cache key
        filter_dict = filters.model_dump() if filters else {}
        sort_dict = sort.model_dump() if sort else {}
        cache_key_data = {**filter_dict, **sort_dict}
        
        # Try cache first
        if use_cache:
            cached = await product_cache.get_product_list(
                pagination.page,
                pagination.page_size,
                cache_key_data
            )
            if cached:
                return PaginatedResponse(**cached)
        
        # Build query
        query = select(Product).where(Product.is_deleted == False)
        count_query = select(func.count(Product.id)).where(Product.is_deleted == False)
        
        # Apply filters
        if filters:
            if filters.name:
                query = query.where(Product.name.ilike(f"%{filters.name}%"))
                count_query = count_query.where(Product.name.ilike(f"%{filters.name}%"))
            
            if filters.category:
                query = query.where(Product.category == filters.category)
                count_query = count_query.where(Product.category == filters.category)
            
            if filters.min_price is not None:
                query = query.where(Product.price >= filters.min_price)
                count_query = count_query.where(Product.price >= filters.min_price)
            
            if filters.max_price is not None:
                query = query.where(Product.price <= filters.max_price)
                count_query = count_query.where(Product.price <= filters.max_price)
            
            if filters.in_stock_only:
                query = query.where(Product.stock > 0)
                count_query = count_query.where(Product.stock > 0)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        if sort:
            sort_column = getattr(Product, sort.sort_by, Product.created_at)
            if sort.sort_order == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(Product.created_at.desc())
        
        # Apply pagination
        query = query.offset(pagination.skip).limit(pagination.page_size)
        
        # Execute query
        result = await db.execute(query)
        products = result.scalars().all()
        
        # Calculate total pages
        total_pages = math.ceil(total / pagination.page_size) if total > 0 else 1
        
        # Build response
        items = [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "price": float(p.price),
                "stock": p.stock,
                "category": p.category,
                "sku": p.sku,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in products
        ]
        
        response_data = {
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total_pages": total_pages
        }
        
        # Cache result
        if use_cache:
            await product_cache.set_product_list(
                pagination.page,
                pagination.page_size,
                response_data,
                cache_key_data
            )
        
        return PaginatedResponse(**response_data)
    
    @staticmethod
    async def update_product(
        db: AsyncSession, 
        product_id: UUID, 
        update_data: ProductUpdate
    ) -> Optional[Product]:
        """
        Update product
        
        Args:
            db: Database session
            product_id: Product UUID
            update_data: Update data
        
        Returns:
            Updated product instance or None
        """
        result = await db.execute(
            select(Product).where(
                Product.id == str(product_id),
                Product.is_deleted == False
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(product, field, value)
        
        await db.flush()
        await db.refresh(product)
        
        # Invalidate cache
        await product_cache.invalidate_product(str(product_id))
        
        return product
    
    @staticmethod
    async def delete_product(db: AsyncSession, product_id: UUID) -> bool:
        """
        Soft delete product
        
        Args:
            db: Database session
            product_id: Product UUID
        
        Returns:
            Success status
        """
        result = await db.execute(
            select(Product).where(
                Product.id == str(product_id),
                Product.is_deleted == False
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            return False
        
        product.soft_delete()
        await db.flush()
        
        # Invalidate cache
        await product_cache.invalidate_product(str(product_id))
        
        return True
    
    @staticmethod
    async def search_products(
        db: AsyncSession,
        query: str,
        pagination: PaginationParams,
        use_cache: bool = True
    ) -> PaginatedResponse:
        """
        Search products by name, description, or SKU
        
        Args:
            db: Database session
            query: Search query
            pagination: Pagination parameters
            use_cache: Whether to use cache
        
        Returns:
            Paginated response with matching products
        """
        # Try cache first
        if use_cache:
            cached = await product_cache.get_search_results(
                query,
                pagination.page,
                pagination.page_size
            )
            if cached:
                return PaginatedResponse(**cached)
        
        # Build search query
        search_term = f"%{query}%"
        base_query = select(Product).where(
            Product.is_deleted == False,
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.sku.ilike(search_term)
            )
        )
        
        # Count query
        count_query = select(func.count(Product.id)).where(
            Product.is_deleted == False,
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.sku.ilike(search_term)
            )
        )
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        paginated_query = base_query.order_by(Product.created_at.desc()).offset(
            pagination.skip
        ).limit(pagination.page_size)
        
        result = await db.execute(paginated_query)
        products = result.scalars().all()
        
        # Calculate total pages
        total_pages = math.ceil(total / pagination.page_size) if total > 0 else 1
        
        # Build response
        items = [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "price": float(p.price),
                "stock": p.stock,
                "category": p.category,
                "sku": p.sku,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in products
        ]
        
        response_data = {
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total_pages": total_pages
        }
        
        # Cache result
        if use_cache:
            await product_cache.set_search_results(
                query,
                pagination.page,
                pagination.page_size,
                response_data
            )
        
        return PaginatedResponse(**response_data)
