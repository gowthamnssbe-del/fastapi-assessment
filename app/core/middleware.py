"""
Middleware Module
Logging and error handling middleware
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging
    
    Logs:
    - Request method, path, and query params
    - Response status code and processing time
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log request
        start_time = time.time()
        
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"Query: {dict(request.query_params)}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Time: {process_time:.2f}ms"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware
    
    Catches unhandled exceptions and returns consistent error responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(
                f"Unhandled exception on {request.method} {request.url.path}: "
                f"{str(exc)}",
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": str(exc) if logger.level == logging.DEBUG else None
                }
            )


class CORSMiddleware:
    """
    CORS middleware configuration helper
    
    Use with FastAPI CORSMiddleware from starlette
    """
    
    @staticmethod
    def get_config() -> dict:
        """Get CORS configuration"""
        return {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
