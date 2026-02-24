"""
User Service
Business logic for user management and authentication
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user import User, UserRole
from ..models.schemas import UserCreate, UserUpdate
from ..core.security import get_password_hash, verify_password


class UserService:
    """Service for user operations"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """
        Create a new user
        
        Args:
            db: Database session
            user_data: User creation data
        
        Returns:
            Created user instance
        """
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            role=UserRole.USER,
            is_active=True
        )
        
        db.add(user)
        await db.flush()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User UUID
        
        Returns:
            User instance or None
        """
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.is_deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            db: Database session
            email: User email
        
        Returns:
            User instance or None
        """
        result = await db.execute(
            select(User).where(
                User.email == email,
                User.is_deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """
        Get user by username
        
        Args:
            db: Database session
            username: Username
        
        Returns:
            User instance or None
        """
        result = await db.execute(
            select(User).where(
                User.username == username,
                User.is_deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password
        
        Args:
            db: Database session
            username: Username
            password: Plain password
        
        Returns:
            User instance if authenticated, None otherwise
        """
        user = await UserService.get_user_by_username(db, username)
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    @staticmethod
    async def update_user(db: AsyncSession, user: User, update_data: UserUpdate) -> User:
        """
        Update user information
        
        Args:
            db: Database session
            user: User instance
            update_data: Update data
        
        Returns:
            Updated user instance
        """
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if "password" in update_dict:
            update_dict["hashed_password"] = get_password_hash(update_dict.pop("password"))
        
        for field, value in update_dict.items():
            setattr(user, field, value)
        
        await db.flush()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def delete_user(db: AsyncSession, user: User) -> None:
        """
        Soft delete user
        
        Args:
            db: Database session
            user: User instance
        """
        user.soft_delete()
        await db.flush()
    
    @staticmethod
    async def update_role(db: AsyncSession, user: User, role: UserRole) -> User:
        """
        Update user role (admin only)
        
        Args:
            db: Database session
            user: User instance
            role: New role
        
        Returns:
            Updated user instance
        """
        user.role = role
        await db.flush()
        await db.refresh(user)
        
        return user
