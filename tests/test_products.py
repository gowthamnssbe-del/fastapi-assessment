"""
Product Tests
Tests for CRUD operations, pagination, filtering, and sorting
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from decimal import Decimal
from uuid import uuid4
from app.models.user import User
from app.models.product import Product
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def test_products(db_session: AsyncSession) -> list[Product]:
    """Create test products"""
    products = [
        Product(
            name="Product A",
            description="Description for product A",
            price=Decimal("19.99"),
            stock=100,
            category="Electronics",
            sku="SKU-A001"
        ),
        Product(
            name="Product B",
            description="Description for product B",
            price=Decimal("29.99"),
            stock=50,
            category="Electronics",
            sku="SKU-B001"
        ),
        Product(
            name="Product C",
            description="Description for product C",
            price=Decimal("9.99"),
            stock=0,
            category="Books",
            sku="SKU-C001"
        ),
    ]
    
    for product in products:
        db_session.add(product)
    
    await db_session.commit()
    
    for product in products:
        await db_session.refresh(product)
    
    return products


class TestProductCreate:
    """Tests for product creation"""
    
    @pytest.mark.asyncio
    async def test_create_product_success(
        self,
        client: AsyncClient,
        admin_auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/products",
            json={
                "name": "New Product",
                "description": "A new product",
                "price": 49.99,
                "stock": 25,
                "category": "Test",
                "sku": "SKU-NEW001"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Product"
        assert float(data["price"]) == 49.99
    
    @pytest.mark.asyncio
    async def test_create_product_unauthorized(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/products",
            json={
                "name": "New Product",
                "price": 49.99,
                "sku": "SKU-NEW002"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_create_product_no_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/products",
            json={
                "name": "New Product",
                "price": 49.99,
                "sku": "SKU-NEW003"
            }
        )
        
        assert response.status_code == 401


class TestProductList:
    """Tests for product listing"""
    
    @pytest.mark.asyncio
    async def test_get_products_success(
        self,
        client: AsyncClient,
        test_products: list[Product]
    ):
        response = await client.get("/api/v1/products")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3
    
    @pytest.mark.asyncio
    async def test_get_products_pagination(
        self,
        client: AsyncClient,
        test_products: list[Product]
    ):
        response = await client.get(
            "/api/v1/products",
            params={"page": 1, "page_size": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page_size"] == 2
    
    @pytest.mark.asyncio
    async def test_get_products_filter_by_category(
        self,
        client: AsyncClient,
        test_products: list[Product]
    ):
        response = await client.get(
            "/api/v1/products",
            params={"category": "Electronics"}
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category"] == "Electronics"
    
    @pytest.mark.asyncio
    async def test_get_products_filter_by_price_range(
        self,
        client: AsyncClient,
        test_products: list[Product]
    ):
        response = await client.get(
            "/api/v1/products",
            params={"min_price": 15.00, "max_price": 30.00}
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert 15.00 <= float(item["price"]) <= 30.00
    
    @pytest.mark.asyncio
    async def test_get_products_filter_in_stock(
        self,
        client: AsyncClient,
        test_products: list[Product]
    ):
        response = await client.get(
            "/api/v1/products",
            params={"in_stock_only": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["stock"] > 0
    
    @pytest.mark.asyncio
    async def test_get_products_sort_by_price(
        self,
        client: AsyncClient,
        test_products: list[Product]
    ):
        response = await client.get(
            "/api/v1/products",
            params={"sort_by": "price", "sort_order": "asc"}
        )
        
        assert response.status_code == 200
        data = response.json()
        if len(data["items"]) > 1:
            prices = [float(item["price"]) for item in data["items"]]
            assert prices == sorted(prices)


class TestProductSearch:
    """Tests for product search"""
    
    @pytest.mark.asyncio
    async def test_search_products(
        self,
        client: AsyncClient,
        test_products: list[Product]
    ):
        response = await client.get(
            "/api/v1/products/search",
            params={"q": "Product"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1
    
    @pytest.mark.asyncio
    async def test_search_products_by_sku(
        self,
        client: AsyncClient,
        test_products: list[Product]
    ):
        response = await client.get(
            "/api/v1/products/search",
            params={"q": "SKU-A001"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestProductDetail:
    """Tests for product detail"""
    
    @pytest.mark.asyncio
    async def test_get_product_by_id(
        self,
        client: AsyncClient,
        test_products: list[Product]
    ):
        product = test_products[0]
        response = await client.get(f"/api/v1/products/{product.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == product.name
    
    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client: AsyncClient):
        fake_id = str(uuid4())
        response = await client.get(f"/api/v1/products/{fake_id}")
        
        assert response.status_code == 404


class TestProductUpdate:
    """Tests for product update"""
    
    @pytest.mark.asyncio
    async def test_update_product_success(
        self,
        client: AsyncClient,
        test_products: list[Product],
        admin_auth_headers: dict
    ):
        product = test_products[0]
        response = await client.put(
            f"/api/v1/products/{product.id}",
            json={"name": "Updated Product", "price": 99.99},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product"
    
    @pytest.mark.asyncio
    async def test_update_product_unauthorized(
        self,
        client: AsyncClient,
        test_products: list[Product],
        auth_headers: dict
    ):
        product = test_products[0]
        response = await client.put(
            f"/api/v1/products/{product.id}",
            json={"name": "Updated"},
            headers=auth_headers
        )
        
        assert response.status_code == 403


class TestProductDelete:
    """Tests for product deletion"""
    
    @pytest.mark.asyncio
    async def test_delete_product_success(
        self,
        client: AsyncClient,
        test_products: list[Product],
        admin_auth_headers: dict
    ):
        product = test_products[0]
        response = await client.delete(
            f"/api/v1/products/{product.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_delete_product_unauthorized(
        self,
        client: AsyncClient,
        test_products: list[Product],
        auth_headers: dict
    ):
        product = test_products[0]
        response = await client.delete(
            f"/api/v1/products/{product.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 403