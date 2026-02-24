"""
RBAC Tests
Tests for Role-Based Access Control
"""
import pytest
from httpx import AsyncClient
from app.models.user import User
from app.models.product import Product
from uuid import uuid4

def str_uuid():
    """Generate string UUID for SQLite compatibility"""
    return str(uuid4())


class TestUserEndpointsRBAC:
    """Tests for RBAC on user endpoints"""
    
    @pytest.mark.asyncio
    async def test_admin_can_list_users(
        self,
        client: AsyncClient,
        admin_auth_headers: dict
    ):
        """Test admin can list all users"""
        response = await client.get(
            "/api/v1/users",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_user_cannot_list_users(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test regular user cannot list all users"""
        response = await client.get(
            "/api/v1/users",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_user_can_view_own_profile(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test user can view their own profile"""
        response = await client.get(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_user_cannot_view_other_profile(
        self,
        client: AsyncClient,
        test_admin: User,
        auth_headers: dict
    ):
        """Test user cannot view another user's profile"""
        response = await client.get(
            f"/api/v1/users/{test_admin.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_can_view_any_profile(
        self,
        client: AsyncClient,
        test_user: User,
        admin_auth_headers: dict
    ):
        """Test admin can view any user's profile"""
        response = await client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_admin_can_delete_user(
        self,
        client: AsyncClient,
        test_user: User,
        admin_auth_headers: dict
    ):
        """Test admin can delete user"""
        response = await client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 204


class TestProductEndpointsRBAC:
    """Tests for RBAC on product endpoints"""
    
    @pytest.mark.asyncio
    async def test_anyone_can_list_products(
        self,
        client: AsyncClient
    ):
        """Test anyone can list products"""
        response = await client.get("/api/v1/products")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_anyone_can_view_product(
        self,
        client: AsyncClient,
        db_session
    ):
        """Test anyone can view product detail"""
        from decimal import Decimal
        
        product = Product(
            id=str_uuid(),
            name="Test Product",
            price=Decimal("10.00"),
            sku="TEST-SKU-001"
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        response = await client.get(f"/api/v1/products/{product.id}")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_admin_can_create_product(
        self,
        client: AsyncClient,
        admin_auth_headers: dict
    ):
        """Test admin can create product"""
        response = await client.post(
            "/api/v1/products",
            json={
                "name": "Test Product",
                "price": 19.99,
                "sku": "TEST-SKU-002"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 201
    
    @pytest.mark.asyncio
    async def test_user_cannot_create_product(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test regular user cannot create product"""
        response = await client.post(
            "/api/v1/products",
            json={
                "name": "Test Product",
                "price": 19.99,
                "sku": "TEST-SKU-003"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_can_update_product(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
        db_session
    ):
        """Test admin can update product"""
        from decimal import Decimal
        
        product = Product(
            id=str_uuid(),
            name="Test Product",
            price=Decimal("10.00"),
            sku="TEST-SKU-004"
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        response = await client.put(
            f"/api/v1/products/{product.id}",
            json={"name": "Updated Product"},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_user_cannot_update_product(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session
    ):
        """Test regular user cannot update product"""
        from decimal import Decimal
        
        product = Product(
            id=str_uuid(),
            name="Test Product",
            price=Decimal("10.00"),
            sku="TEST-SKU-005"
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        response = await client.put(
            f"/api/v1/products/{product.id}",
            json={"name": "Updated Product"},
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_can_delete_product(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
        db_session
    ):
        """Test admin can delete product"""
        from decimal import Decimal
        
        product = Product(
            id=str_uuid(),
            name="Test Product",
            price=Decimal("10.00"),
            sku="TEST-SKU-006"
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        response = await client.delete(
            f"/api/v1/products/{product.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 204


class TestInactiveUser:
    """Tests for inactive user access"""
    
    @pytest.mark.asyncio
    async def test_inactive_user_cannot_login(
        self,
        client: AsyncClient,
        db_session
    ):
        """Test inactive user cannot login"""
        from app.core.security import get_password_hash
        from app.models.user import User, UserRole
        
        inactive_user = User(
            id=str_uuid(),
            email="inactive@example.com",
            username="inactiveuser",
            hashed_password=get_password_hash("TestPass123"),
            role=UserRole.USER,
            is_active=False
        )
        db_session.add(inactive_user)
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "inactiveuser",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 401