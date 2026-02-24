"""
Base Model with Common Fields
Provides UUID primary key, timestamps, and soft delete functionality
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.orm import declared_attr
from app.db.database import Base


class BaseModel(Base):
    """
    Abstract base model with common fields
    
    Features:
    - UUID primary key (stored as String for SQLite compatibility)
    - Created/Updated timestamps
    - Soft delete support
    """
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    def soft_delete(self):
        """Mark record as deleted without removing from database"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
    
    def restore(self):
        """Restore a soft-deleted record"""
        self.is_deleted = False
        self.updated_at = datetime.utcnow()