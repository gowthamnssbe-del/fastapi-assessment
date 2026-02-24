"""
Pytest Configuration
Test fixtures for async testing with database and Redis mocking
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.db.database import Base, get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash, create_access_token
from app.cache.redis_client import redis_client


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database dependency override"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock Redis client
    with patch.object(redis_client, 'get', new_callable=AsyncMock) as mock_get, \
         patch.object(redis_client, 'set', new_callable=AsyncMock) as mock_set, \
         patch.object(redis_client, 'delete', new_callable=AsyncMock) as mock_delete, \
         patch.object(redis_client, 'delete_pattern', new_callable=AsyncMock) as mock_delete_pattern:
        
        mock_get.return_value = None
        mock_set.return_value = True
        mock_delete.return_value = True
        mock_delete_pattern.return_value = 0
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user"""
    user = User(
        id=str(__import__('uuid').uuid4()),  # Convert to string
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPass123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create test admin user"""
    admin = User(
        id=str(__import__('uuid').uuid4()),  # Convert to string
        email="admin@example.com",
        username="adminuser",
        hashed_password=get_password_hash("AdminPass123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
def user_token(test_user: User) -> str:
    """Create access token for test user"""
    return create_access_token({"sub": str(test_user.id), "role": test_user.role.value})


@pytest_asyncio.fixture
def admin_token(test_admin: User) -> str:
    """Create access token for test admin"""
    return create_access_token({"sub": str(test_admin.id), "role": test_admin.role.value})


@pytest_asyncio.fixture
def auth_headers(user_token: str) -> dict:
    """Create authorization headers for user"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest_asyncio.fixture
def admin_auth_headers(admin_token: str) -> dict:
    """Create authorization headers for admin"""
    return {"Authorization": f"Bearer {admin_token}"}