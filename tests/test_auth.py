"""
Authentication Tests
Tests for registration, login, token refresh, and authorization
"""
import pytest
from httpx import AsyncClient
from app.models.user import User


class TestRegistration:
    """Tests for user registration"""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["role"] == "user"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "different",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate username"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "different@example.com",
                "username": test_user.username,
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "password": "weak"
            }
        )
        
        assert response.status_code == 422


class TestLogin:
    """Tests for user login"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_username(self, client: AsyncClient):
        """Test login with invalid username"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "SomePass123"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Test login with invalid password"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "WrongPass123"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_json(self, client: AsyncClient, test_user: User):
        """Test JSON login endpoint"""
        response = await client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "testuser",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


class TestTokenRefresh:
    """Tests for token refresh"""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user: User):
        """Test successful token refresh"""
        # First login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "TestPass123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token"""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401


class TestGetCurrentUser:
    """Tests for getting current user info"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, 
        client: AsyncClient, 
        test_user: User,
        auth_headers: dict
    ):
        """Test getting current user info"""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test getting current user without token"""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
