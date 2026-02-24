"""
Product Endpoints
CRUD operations with pagination, filtering, and sorting
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from ...db.database import get_db
from ...models.schemas import (
    ProductCreate, ProductUpdate, ProductResponse,
    PaginatedResponse, PaginationParams, ProductFilter, ProductSort
)
from ...services.product_service import ProductService
from ...utils.auth import get_current_user, get_current_admin_user
from ...models.user import User

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new product (Admin only)
    
    Args:
        product_data: Product creation data
        db: Database session
        current_user: Current admin user
    
    Returns:
        Created product
    """
    product = await ProductService.create_product(db, product_data)
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category=product.category,
        sku=product.sku,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.get("", response_model=PaginatedResponse)
async def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[Decimal] = Query(None, description="Minimum price"),
    max_price: Optional[Decimal] = Query(None, description="Maximum price"),
    in_stock_only: bool = Query(False, description="Show only in-stock products"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated products with filtering and sorting
    
    Supports:
    - Pagination (page, page_size)
    - Filtering (name, category, price range, stock)
    - Sorting (by name, price, created_at, stock)
    
    Args:
        page: Page number
        page_size: Items per page
        name: Filter by name
        category: Filter by category
        min_price: Minimum price filter
        max_price: Maximum price filter
        in_stock_only: Show only in-stock
        sort_by: Sort field
        sort_order: Sort direction
        db: Database session
    
    Returns:
        Paginated list of products
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    
    filters = ProductFilter(
        name=name,
        category=category,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only
    ) if any([name, category, min_price, max_price, in_stock_only]) else None
    
    sort = ProductSort(sort_by=sort_by, sort_order=sort_order)
    
    return await ProductService.get_products(
        db,
        pagination=pagination,
        filters=filters,
        sort=sort
    )


@router.get("/search", response_model=PaginatedResponse)
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search products by name, description, or SKU
    
    Args:
        q: Search query
        page: Page number
        page_size: Items per page
        db: Database session
    
    Returns:
        Paginated search results
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    
    return await ProductService.search_products(db, q, pagination)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get product by ID
    
    Args:
        product_id: Product UUID
        db: Database session
    
    Returns:
        Product details
    
    Raises:
        HTTPException: If product not found
    """
    product = await ProductService.get_product_by_id(db, product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductResponse(
        id=UUID(product["id"]),
        name=product["name"],
        description=product["description"],
        price=Decimal(str(product["price"])),
        stock=product["stock"],
        category=product["category"],
        sku=product["sku"],
        created_at=product["created_at"],
        updated_at=product["updated_at"]
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    update_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update product (Admin only)
    
    Args:
        product_id: Product UUID
        update_data: Update data
        db: Database session
        current_user: Current admin user
    
    Returns:
        Updated product
    
    Raises:
        HTTPException: If product not found
    """
    product = await ProductService.update_product(db, product_id, update_data)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category=product.category,
        sku=product.sku,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Soft delete product (Admin only)
    
    Args:
        product_id: Product UUID
        db: Database session
        current_user: Current admin user
    
    Raises:
        HTTPException: If product not found
    """
    success = await ProductService.delete_product(db, product_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return None
