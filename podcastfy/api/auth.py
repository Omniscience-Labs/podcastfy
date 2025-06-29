"""
Authentication and rate limiting middleware for the Podcastfy API.

This module provides API key authentication, rate limiting, and request tracking.
"""

import os
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from functools import wraps

from fastapi import HTTPException, Request, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis
from sqlalchemy.orm import Session

from .database import get_db
from .models import ErrorResponse
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize Redis client
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Security scheme
security = HTTPBearer()


class APIKey:
    """API Key management class."""
    
    def __init__(self, key: str, name: str, rate_limit: int = 100, 
                 quota_daily: int = 1000, is_active: bool = True):
        self.key = key
        self.name = name
        self.rate_limit = rate_limit  # requests per minute
        self.quota_daily = quota_daily  # daily request quota
        self.is_active = is_active
        self.created_at = datetime.utcnow()
    
    @staticmethod
    def generate_key() -> str:
        """Generate a secure API key."""
        return f"pk_{os.urandom(32).hex()}"
    
    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()


class RateLimiter:
    """Rate limiting implementation using Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def is_allowed(self, key: str, limit: int, window: int = 60) -> Tuple[bool, Dict]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            key: Unique identifier (API key)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, metadata)
        """
        now = time.time()
        pipeline = self.redis.pipeline()
        pipeline.zremrangebyscore(key, 0, now - window)
        pipeline.zadd(key, {str(now): now})
        pipeline.zcount(key, now - window, now)
        pipeline.expire(key, window + 1)
        results = pipeline.execute()
        
        current_requests = results[2]
        
        return current_requests <= limit, {
            "limit": limit,
            "remaining": max(0, limit - current_requests),
            "reset": int(now + window)
        }
    
    def get_daily_usage(self, key: str) -> int:
        """Get daily usage count for an API key."""
        today = datetime.utcnow().strftime("%Y%m%d")
        daily_key = f"daily:{key}:{today}"
        return int(self.redis.get(daily_key) or 0)
    
    def increment_daily_usage(self, key: str) -> int:
        """Increment daily usage count."""
        today = datetime.utcnow().strftime("%Y%m%d")
        daily_key = f"daily:{key}:{today}"
        pipeline = self.redis.pipeline()
        pipeline.incr(daily_key)
        pipeline.expire(daily_key, 86400)  # 24 hours
        results = pipeline.execute()
        return results[0]


# Initialize rate limiter
rate_limiter = RateLimiter(redis_client)


def get_api_key_from_header(
    authorization: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract API key from Authorization header."""
    return authorization.credentials


async def verify_api_key(
    api_key: str = Depends(get_api_key_from_header),
    db: Session = Depends(get_db)
) -> APIKey:
    """
    Verify API key and return associated metadata.
    
    This is a simplified version. In production, you would:
    1. Store API keys in database
    2. Cache valid keys in Redis
    3. Track usage statistics
    """
    # For demo purposes, we'll check against environment variables
    # In production, query from database
    valid_keys = {
        os.getenv("DEMO_API_KEY", "pk_demo123"): APIKey(
            key=os.getenv("DEMO_API_KEY", "pk_demo123"),
            name="demo",
            rate_limit=10,
            quota_daily=100
        ),
        os.getenv("PROD_API_KEY", "pk_prod456"): APIKey(
            key=os.getenv("PROD_API_KEY", "pk_prod456"),
            name="production",
            rate_limit=100,
            quota_daily=10000
        )
    }
    
    if api_key not in valid_keys:
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    key_info = valid_keys[api_key]
    
    if not key_info.is_active:
        raise HTTPException(
            status_code=403,
            detail="API key is inactive"
        )
    
    # Check rate limit
    is_allowed, rate_limit_info = rate_limiter.is_allowed(
        f"rate:{api_key}", 
        key_info.rate_limit
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                "X-RateLimit-Reset": str(rate_limit_info["reset"]),
            }
        )
    
    # Check daily quota
    daily_usage = rate_limiter.get_daily_usage(api_key)
    if daily_usage >= key_info.quota_daily:
        raise HTTPException(
            status_code=429,
            detail="Daily quota exceeded",
            headers={
                "X-Quota-Limit": str(key_info.quota_daily),
                "X-Quota-Used": str(daily_usage),
                "X-Quota-Reset": str(int((datetime.utcnow() + timedelta(days=1)).timestamp()))
            }
        )
    
    # Increment daily usage
    rate_limiter.increment_daily_usage(api_key)
    
    return key_info


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for request tracking and logging."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = f"req_{os.urandom(16).hex()}"
        request.state.request_id = request_id
        
        # Log request
        logger.info(f"Request {request_id}: {request.method} {request.url.path}")
        
        # Add security headers
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            # Log response
            duration = time.time() - start_time
            logger.info(f"Request {request_id} completed in {duration:.3f}s with status {response.status_code}")
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Request {request_id} failed after {duration:.3f}s: {str(e)}")
            
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error="InternalServerError",
                    message="An unexpected error occurred",
                    request_id=request_id
                ).dict()
            )


def require_api_key(scopes: Optional[list] = None):
    """Decorator to require API key authentication for endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # API key verification is handled by dependency injection
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class APIKeyManager:
    """Manage API keys in database."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_key(self, name: str, rate_limit: int = 100, 
                   quota_daily: int = 1000) -> str:
        """Create a new API key."""
        key = APIKey.generate_key()
        # In production, save to database
        # For now, just return the key
        logger.info(f"Created API key for {name}")
        return key
    
    def revoke_key(self, key: str) -> bool:
        """Revoke an API key."""
        # In production, update database
        logger.info(f"Revoked API key {key[:8]}...")
        return True
    
    def get_usage_stats(self, key: str) -> Dict:
        """Get usage statistics for an API key."""
        daily_usage = rate_limiter.get_daily_usage(key)
        return {
            "daily_usage": daily_usage,
            "last_used": datetime.utcnow().isoformat()
        } 