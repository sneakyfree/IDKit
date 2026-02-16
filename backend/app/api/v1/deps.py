"""
API Dependencies

Common dependencies for FastAPI route handlers including:
- Database session
- Current user authentication
- Admin authorization
- Rate limiting
"""

from typing import Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.models.database import async_session_factory
from app.config import settings


# Security scheme
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.
    
    Yields an async SQLAlchemy session and ensures it's closed after the request.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current authenticated user from JWT token.
    
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    # Import here to avoid circular imports
    from app.models.user import User
    from sqlalchemy import select
    from uuid import UUID as UUIDType
    
    # Convert string user_id to UUID for database query
    try:
        user_uuid = UUIDType(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )
    
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Optionally get the current user (returns None if not authenticated).
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def require_admin(
    current_user = Depends(get_current_user),
):
    """
    Require the current user to be an admin.
    
    Raises:
        HTTPException: 403 if user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_verified(
    current_user = Depends(get_current_user),
):
    """
    Require the current user to be verified.
    
    Raises:
        HTTPException: 403 if user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    return current_user


class RateLimitDep:
    """
    Rate limiting dependency using Redis sliding window.

    Usage:
        @router.get("/endpoint")
        async def endpoint(rate_limit: bool = Depends(RateLimitDep(requests=10, period=60))):
            ...
    """

    def __init__(self, requests: int = 100, period: int = 60):
        self.requests = requests
        self.period = period

    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ) -> bool:
        """Check rate limit using Redis sliding window counter."""
        import time

        try:
            from app.main import redis_client
        except (ImportError, AttributeError):
            if settings.debug:
                return True
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limiting service unavailable",
            )

        if redis_client is None:
            if settings.debug:
                return True
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limiting service unavailable",
            )

        # Identify client by JWT subject or fallback to "anon"
        client_id = "anon"
        if credentials:
            try:
                payload = jwt.decode(
                    credentials.credentials,
                    settings.jwt_secret_key,
                    algorithms=["HS256"],
                )
                client_id = payload.get("sub", "anon")
            except Exception:
                client_id = "anon"

        key = f"ratelimit:{client_id}:{self.period}"
        now = time.time()

        try:
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now - self.period)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self.period)
            results = await pipe.execute()
            request_count = results[2]
        except Exception:
            if settings.debug:
                return True
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limiting service unavailable",
            )

        if request_count > self.requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {self.requests} requests per {self.period}s.",
                headers={"Retry-After": str(self.period)},
            )

        return True


# Commonly used dependencies
def get_pagination(
    skip: int = 0,
    limit: int = 100,
):
    """
    Pagination parameters dependency.
    """
    if limit > 1000:
        limit = 1000
    if skip < 0:
        skip = 0
    return {"skip": skip, "limit": limit}
