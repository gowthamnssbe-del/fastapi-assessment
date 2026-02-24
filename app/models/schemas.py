"""
Pydantic Schemas
Data validation and serialization schemas for API requests/responses
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# ==================== Base Schemas ====================

class BaseResponseSchema(BaseModel):
    """Base schema for responses with common fields"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for user updates"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(BaseResponseSchema):
    """Schema for user response"""
    email: str
    username: str
    role: str
    is_active: bool


class UserInDB(UserResponse):
    """Schema for user in database (includes sensitive data)"""
    hashed_password: str


# ==================== Auth Schemas ====================

class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for decoded token payload"""
    sub: str  # user_id
    exp: datetime
    type: str  # 'access' or 'refresh'


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str


# ==================== Product Schemas ====================

class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    stock: int = Field(default=0, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    sku: str = Field(..., min_length=1, max_length=50)


class ProductCreate(ProductBase):
    """Schema for product creation"""
    pass


class ProductUpdate(BaseModel):
    """Schema for product updates"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)


class ProductResponse(BaseResponseSchema):
    """Schema for product response"""
    name: str
    description: Optional[str]
    price: Decimal
    stock: int
    category: Optional[str]
    sku: str
    
    class Config:
        from_attributes = True


# ==================== Pagination Schemas ====================

class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database query"""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Generic paginated response schema"""
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        arbitrary_types_allowed = True


class ProductFilter(BaseModel):
    """Schema for product filtering"""
    name: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    in_stock_only: bool = False


class ProductSort(BaseModel):
    """Schema for product sorting"""
    sort_by: str = "created_at"  # name, price, created_at, stock
    sort_order: str = "desc"  # asc or desc
