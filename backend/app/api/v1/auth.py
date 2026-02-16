"""
Authentication API Endpoints

Handles social login (Google, Apple) and JWT token management.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import RedirectResponse
from jose import jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import DB, CurrentUser, get_db
from app.models.user import User
from app.models.feed import UserProfile

router = APIRouter()


# ==================== Schemas ====================


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User info response."""

    id: uuid.UUID
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    is_verified: bool
    subscription_tier: str

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    """Profile info response."""

    id: uuid.UUID
    username: str
    display_name: str
    bio: Optional[str]
    avatar_url: Optional[str]
    follower_count: int
    following_count: int
    post_count: int
    is_verified: bool

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    """Current user with profile."""

    user: UserResponse
    profile: Optional[ProfileResponse]


class RegisterRequest(BaseModel):
    """Email/password registration."""

    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Email/password login."""

    email: EmailStr
    password: str


# ==================== Token Utilities ====================


def create_access_token(user_id: uuid.UUID) -> str:
    """Create JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Create JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_tokens(user_id: uuid.UUID) -> TokenResponse:
    """Create access and refresh tokens."""
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


# ==================== OAuth Helpers ====================


def get_google_client() -> AsyncOAuth2Client:
    """Create Google OAuth client."""
    return AsyncOAuth2Client(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
    )


async def get_or_create_user(
    db: AsyncSession,
    email: str,
    oauth_provider: str,
    oauth_provider_id: str,
    full_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> User:
    """Get existing user or create new one."""
    # Try to find by OAuth provider ID
    result = await db.execute(
        select(User).where(
            User.oauth_provider == oauth_provider,
            User.oauth_provider_id == oauth_provider_id,
        )
    )
    user = result.scalar_one_or_none()

    if user:
        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        return user

    # Try to find by email (user might have logged in with different provider)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Link this OAuth provider to existing account
        user.oauth_provider = oauth_provider
        user.oauth_provider_id = oauth_provider_id
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        return user

    # Create new user
    user = User(
        email=email,
        oauth_provider=oauth_provider,
        oauth_provider_id=oauth_provider_id,
        full_name=full_name,
        avatar_url=avatar_url,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()

    # Create profile with auto-generated username
    username = await generate_unique_username(db, email)
    profile = UserProfile(
        user_id=user.id,
        username=username,
        display_name=full_name or email.split("@")[0],
        avatar_url=avatar_url,
    )
    db.add(profile)

    await db.commit()
    await db.refresh(user)

    return user


async def generate_unique_username(db: AsyncSession, email: str) -> str:
    """Generate unique username from email."""
    base_username = email.split("@")[0].lower()
    # Remove non-alphanumeric characters
    base_username = "".join(c for c in base_username if c.isalnum())

    # Check if username exists
    username = base_username
    counter = 1

    while True:
        result = await db.execute(
            select(UserProfile).where(UserProfile.username == username)
        )
        if result.scalar_one_or_none() is None:
            break

        username = f"{base_username}{counter}"
        counter += 1

    return username


# ==================== Endpoints ====================


@router.get("/google")
async def google_login():
    """Initiate Google OAuth login."""
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )

    client = get_google_client()
    authorization_url, state = client.create_authorization_url(
        "https://accounts.google.com/o/oauth2/v2/auth",
        scope=["openid", "email", "profile"],
    )

    # In production, store state in session/Redis for validation
    return RedirectResponse(url=authorization_url)


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback."""
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )

    client = get_google_client()

    try:
        # Exchange code for token
        token = await client.fetch_token(
            "https://oauth2.googleapis.com/token",
            code=code,
        )

        # Get user info
        client.token = token
        resp = await client.get("https://www.googleapis.com/oauth2/v3/userinfo")
        user_info = resp.json()

        # Create or get user
        user = await get_or_create_user(
            db=db,
            email=user_info["email"],
            oauth_provider="google",
            oauth_provider_id=user_info["sub"],
            full_name=user_info.get("name"),
            avatar_url=user_info.get("picture"),
        )

        # Create tokens
        tokens = create_tokens(user.id)

        # Redirect to frontend with tokens
        # In production, use secure cookies or redirect with short-lived code
        frontend_url = f"{settings.frontend_url}/auth/callback"
        redirect_url = f"{frontend_url}?access_token={tokens.access_token}&refresh_token={tokens.refresh_token}"

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {str(e)}",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(
            refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = uuid.UUID(payload["sub"])

        # Verify user exists and is active
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return create_tokens(user.id)

    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get("/me", response_model=MeResponse)
async def get_current_user_info(
    current_user: CurrentUser,
    db: DB,
):
    """Get current authenticated user info."""
    # Get profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    return MeResponse(
        user=UserResponse.model_validate(current_user),
        profile=ProfileResponse.model_validate(profile) if profile else None,
    )


@router.post("/logout")
async def logout(response: Response):
    """
    Logout user.

    Note: With JWT, logout is mainly handled client-side by removing tokens.
    This endpoint can be used to clear cookies if using cookie-based auth.
    """
    # Clear any cookies if using them
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "Logged out successfully"}


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new account with email and password."""
    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    import bcrypt

    hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()

    user = User(
        email=body.email,
        password_hash=hashed,
        oauth_provider="email",
        oauth_provider_id=body.email,
        full_name=body.full_name,
    )
    db.add(user)
    await db.flush()

    # Auto-create profile
    username = await generate_unique_username(db, body.email)
    profile = UserProfile(
        user_id=user.id,
        username=username,
        display_name=body.full_name or body.email.split("@")[0],
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)

    return create_tokens(user.id)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    import bcrypt

    if not bcrypt.checkpw(body.password.encode(), user.password_hash.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    return create_tokens(user.id)

