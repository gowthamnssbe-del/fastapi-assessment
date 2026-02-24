
"""
Product Model
Represents products with UUID, pricing, and inventory management
"""
from sqlalchemy import Column, String, Text, Numeric, Integer
from decimal import Decimal
from uuid import uuid4
from .base import BaseModel


class Product(BaseModel):
    """
    Product model for inventory management
    """
    __tablename__ = "products"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    stock = Column(Integer, nullable=False, default=0)
    category = Column(String(100), nullable=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    
    def __repr__(self):
        return f"<Product {self.name}>"
    
    @property
    def price_float(self) -> float:
        return float(self.price)
    
    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0