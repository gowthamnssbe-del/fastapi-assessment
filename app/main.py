"""
FastAPI Application Entry Point
Main application with middleware and lifecycle events
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import LoggingMiddleware, ErrorHandlingMiddleware
from app.api.router import api_router
from app.db.database import init_db, close_db
from app.cache.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    
    Handles:
    - Database initialization
    - Redis connection
    - Cleanup on shutdown
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize database
    await init_db()
    print("Database initialized")
    
    # Connect to Redis
    await redis_client.connect()
    print("Redis connected")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    
    # Close Redis connection
    await redis_client.disconnect()
    print("Redis disconnected")
    
    # Close database connections
    await close_db()
    print("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    FastAPI Assessment - Technical Assessment for Python FastAPI Developer
    
    ## Features
    
    * **Authentication**: OAuth2 password flow with JWT tokens
    * **Authorization**: Role-based access control (RBAC)
    * **Products**: CRUD operations with pagination, filtering, sorting
    * **Caching**: Redis caching for improved performance
    * **Clean Architecture**: Multi-layer structure with dependency injection
    
    ## Endpoints
    
    * `/api/v1/auth` - Authentication endpoints
    * `/api/v1/products` - Product management
    * `/api/v1/users` - User management (admin)
    """,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
