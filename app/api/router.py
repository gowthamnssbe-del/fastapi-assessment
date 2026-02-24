"""
API Router
Combines all endpoint routers
"""
from fastapi import APIRouter
from .endpoints import auth, products, users

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(users.router)
