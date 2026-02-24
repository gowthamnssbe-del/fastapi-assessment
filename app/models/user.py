"""
User Model
Represents application users with role-based access control
"""
from sqlalchemy import Column, String, Boolean, Enum
import enum
from .base import BaseModel


class UserRole(str, enum.Enum):
    """User role enumeration for RBAC"""
    ADMIN = "admin"
    USER = "user"


class User(BaseModel):
    """
    User model for authentication and authorization
    
    Attributes:
        email: Unique user email
        username: Unique username
        hashed_password: Bcrypt hashed password
        role: User role (admin/user)
        is_active: Account active status
    """
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN
